from kiteconnect import KiteConnect
import os
import traceback
import json
import login_kite
import kill_switch

current_file_path = os.path.dirname(os.path.realpath(__file__))


def get_client_doc_from_json(client_id):
   try:
       json_file = os.path.join(current_file_path,'credentials.json')
       with open(json_file) as f:
           data = json.load(f)
           return data[client_id]
   except Exception as e:
       traceback.print_exc()

def save_field_to_json(client_id, field, value):
    try:
        json_file = os.path.join(current_file_path,'credentials.json')
        with open(json_file) as f:
            data = json.load(f)
            data[client_id][field] = value
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        traceback.print_exc()


def get_kite_client(client_id):

    api_key = get_client_doc_from_json(client_id)['api_key']
    global kite
    kite = KiteConnect(api_key=api_key)
    try:
        access_token = get_client_doc_from_json(client_id)['access_token']
        kite.set_access_token(access_token=access_token)
        profile = kite.profile()
        print("Access Token is valid, fetched from json.")
        print(profile)
    except Exception as e:
        try:
            access_token = login_kite.login(client_id)
            kite.set_access_token(access_token=access_token)
            profile = kite.profile()
            print(profile)
            save_field_to_json(client_id, 'access_token', access_token)
        except:
            traceback.print_exc()
            print("Error in login")
            exit(0)

    return kite
    
def get_positions_mtm():
    try:
        positions = kite.positions()
        print(positions)
        mtm = 0
        for position in positions['net']:

            if 'NIFTY' in position['tradingsymbol'] or 'BANKNIFTY' in position['tradingsymbol']:
                print(position)
                symbol = position['tradingsymbol']
                pos_qty = position['buy_quantity'] - position['sell_quantity']
                ltp_symbol = position['exchange'] + ':' + symbol
                ltp = kite.ltp([ltp_symbol])
                print(ltp)
                
                # pnl = (sellValue - buyValue) + (netQuantity * lastPrice * multiplier);
                mtm += (position['sell_value'] - position['buy_value']) + (pos_qty * ltp[ltp_symbol]['last_price'] * position['multiplier'])
        return mtm
    except:
        traceback.print_exc()
        return 0
    
def cancel_all_orders():
    try:
        orders = kite.orders()
        orders = [order for order in orders if order['status'] == 'OPEN']
        for order in orders:
            print(order)
            if 'NIFTY' in order['tradingsymbol'] or 'BANKNIFTY' in order['tradingsymbol']:
                kite.cancel_order(variety=order['variety'],order_id=order['order_id'])
    except:
        traceback.print_exc()

def exit_all_positions():
    try:
        positions = kite.positions()
        positions = [position for position in positions['net'] if ('NIFTY' in position['tradingsymbol'] or 'BANKNIFTY' in position['tradingsymbol']) and position['quantity'] != 0]
        for position in positions:
            kite.place_order(
                variety='regular',
                exchange=position['exchange'],
                tradingsymbol=position['tradingsymbol'],
                transaction_type='SELL',
                quantity=abs(position['quantity']),
                order_type='MARKET',
                product='NRML'
                )
    except:
        traceback.print_exc()

if __name__ == '__main__':
    kite = get_kite_client("XQQ563")
    MTM = get_positions_mtm()
    print(MTM)
    if MTM <= -40:
        cancel_all_orders()
        exit_all_positions()
        kill_switch.main("XQQ563")
