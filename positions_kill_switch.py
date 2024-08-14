from kiteconnect import KiteConnect
import os
import sys
import time
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
import traceback
import json
import login_kite
import kill_switch
import get_logger
import datetime as dt
import pytz
import sqlite3

logger = get_logger.get_logger("positions_kill_switch")

current_file_path = os.path.dirname(os.path.realpath(__file__))


def get_client_doc_from_json(client_id):
    try:
        json_file = os.path.join(current_file_path, 'credentials.json')
        with open(json_file) as f:
            data = json.load(f)
            return data[client_id]
    except Exception as e:
        logger.error(f"Error reading client document for {client_id}: {traceback.format_exc()}")
        return None


def save_field_to_json(client_id, field, value):
    try:
        json_file = os.path.join(current_file_path, 'credentials.json')
        with open(json_file) as f:
            data = json.load(f)
            data[client_id][field] = value
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)
        logger.info(f"Successfully saved {field} for {client_id} in credentials.json")
    except Exception as e:
        logger.error(f"Error saving field to JSON for {client_id}: {traceback.format_exc()}")

def save_data_to_sqllite(client_id, field, value):
    try:
        conn = sqlite3.connect('client_data.db')
        c = conn.cursor()
        c.execute(f'''CREATE TABLE IF NOT EXISTS clients (client_id TEXT PRIMARY KEY, loss_threshold REAL);''')
        c.execute(f"INSERT OR REPLACE INTO clients (client_id, {field}) VALUES (?, ?)", (client_id, value))
        conn.commit()
        conn.close()
        logger.info(f"Successfully saved {field} for {client_id} in SQLite")
    except:
        logger.error(f"Error saving field to SQLite for {client_id}: {traceback.format_exc()}")
        traceback.print_exc()

def get_data_from_sqllite(client_id, field):
    try:
        conn = sqlite3.connect('client_data.db')
        c = conn.cursor()
        c.execute(f"SELECT {field} FROM clients WHERE client_id = ?", (client_id,))
        value = c.fetchone()[0]
        conn.close()
        return value
    except:
        logger.error(f"Error fetching field from SQLite for {client_id}: {traceback.format_exc()}")
        traceback.print_exc()

def get_kite_client(client_id):
    api_key = get_client_doc_from_json(client_id)['api_key']
    global kite
    kite = KiteConnect(api_key=api_key)
    try:
        access_token = get_client_doc_from_json(client_id)['access_token']
        kite.set_access_token(access_token=access_token)
        profile = kite.profile()
        logger.info(f"Access Token is valid, fetched from json for {client_id}. Profile: {profile}")
    except Exception as e:
        logger.error(f"Error with access token for {client_id}, attempting login: {traceback.format_exc()}")
        try:
            access_token = login_kite.login(client_id)
            kite.set_access_token(access_token=access_token)
            profile = kite.profile()
            logger.info(f"Successfully logged in and retrieved profile for {client_id}. Profile: {profile}")
            save_field_to_json(client_id, 'access_token', access_token)
        except:
            logger.error(f"Error in login for {client_id}: {traceback.format_exc()}")
            sys.exit(0)

    return kite


def get_positions_mtm():
    try:
        positions = kite.positions()
        logger.info(f"Fetched positions: {positions}")
        mtm = 0.0
        for position in positions['net']:
            if 'NIFTY' in position['tradingsymbol'] or 'BANKNIFTY' in position['tradingsymbol']:
                logger.info(f"Processing position: {position}")
                symbol = position['tradingsymbol']
                pos_qty = position['buy_quantity'] - position['sell_quantity']
                ltp_symbol = f"{position['exchange']}:{symbol}"
                ltp = kite.ltp([ltp_symbol])
                logger.info(f"Fetched LTP for {ltp_symbol}: {ltp}")
                
                mtm += (position['sell_value'] - position['buy_value']) + (pos_qty * ltp[ltp_symbol]['last_price'] * position['multiplier'])
        return mtm
    except Exception as e:
        logger.error(f"Error calculating MTM: {traceback.format_exc()}")
        return 0


def cancel_all_orders():
    try:
        orders = kite.orders()
        open_orders = [order for order in orders if order['status'] == 'OPEN']
        for order in open_orders:
            logger.info(f"Cancelling order: {order}")
            if 'NIFTY' in order['tradingsymbol'] or 'BANKNIFTY' in order['tradingsymbol']:
                kite.cancel_order(variety=order['variety'], order_id=order['order_id'])
    except Exception as e:
        logger.error(f"Error cancelling orders: {traceback.format_exc()}")


def exit_all_positions():
    try:
        positions = kite.positions()
        open_positions = [position for position in positions['net'] if ('NIFTY' in position['tradingsymbol'] or 'BANKNIFTY' in position['tradingsymbol']) and position['quantity'] != 0]
        for position in open_positions:
            logger.info(f"Exiting position: {position}")
            kite.place_order(
                variety='regular',
                exchange=position['exchange'],
                tradingsymbol=position['tradingsymbol'],
                transaction_type='SELL',
                quantity=abs(position['quantity']),
                order_type='MARKET',
                product='NRML'
            )
    except Exception as e:
        logger.error(f"Error exiting positions: {traceback.format_exc()}")


if __name__ == '__main__':
    start_time = time.time()
    try:
        save_loss_threshold = False
        ist = pytz.timezone('Asia/Kolkata')
        now = dt.datetime.now(ist)
        if now.hour == 9 and now.minute == 15 and now.second < 20:
            save_loss_threshold = True


        json_file = os.path.join(current_file_path, 'credentials.json')
        with open(json_file) as f:
            data = json.load(f)
            data = dict(data)
            for client_id in data.keys():
                if save_loss_threshold:
                    LT = get_client_doc_from_json(client_id)['loss_threshold']
                    if type(LT) in [int, float]:
                        save_data_to_sqllite(client_id, 'loss_threshold', LT)
                    else:
                        logger.error(f"Loss Threshold for {client_id} is not a number: {LT}")

                loss_threshold = float(get_data_from_sqllite(client_id, 'loss_threshold'))
                kite = get_kite_client(client_id)
                MTM = 0.0
                MTM = float(get_positions_mtm())
                logger.info(f"Current MTM for {client_id}: {MTM} ; Loss Threshold: {loss_threshold}")

                if MTM <= loss_threshold * -1:
                    cancel_all_orders()
                    exit_all_positions()
                    # kill_switch.main(client_id) # This will turn off the Segment. (To Turn on, remove the comment (the hash and space before kill_switch.main(client_id)))
            save_loss_threshold = False
    except Exception as e:
        logger.error(f"Error reading credentials.json: {traceback.format_exc()}")
    end_time = time.time()
    logger.info(f"Time taken to execute: {end_time - start_time:.2f} seconds")
