#!/usr/local/bin/python3
# coding: UTF-8
# Author: David
# Email: youchen.du@gmail.com
# Created: 2016-12-17 10:12
# Last modified: 2016-12-31 10:00
# Filename: feature_extract.py
# Description:
import argparse

from datetime import timedelta
from datetime import datetime
from datetime import date
from logging import info
from collections import defaultdict
from functools import partial

from utils import load_from_file, save_to_file, file_retrive
from utils import Progress, timeit, d1, date_1217


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('w_size', metavar='window_size', type=int,
                        help='The scale of the shift window')
    parser.add_argument('dp', metavar='data_set_name', type=str,
                        help='The name of the data set')
    parser.add_argument(
        '--cache', default=1, type=int, metavar='cache_type',
        help='Use 0 force to generate user-item relations, default is 1')

    args = parser.parse_args()

    w_size = args.w_size
    data_path = args.dp
    cache = args.cache

    if w_size < 0:
        raise ValueError("Wrong window size.")

    return w_size, data_path, cache

def extract_item_status(user_items):
    """
        item_status is a dict where data are devided into groups by
        date -> iid -> behavior_type
    """
    info('Extracting item status')
    item_status = defaultdict(
        partial(defaultdict,
                partial(defaultdict,
                        partial(defaultdict, int))))
    p = Progress(len(user_items.keys()))
    for uid, records in user_items.items():
        p.next()
        for uid, iid, bt, gps, cate, date in records:
            item_status[date.date()][cate][iid][bt] += 1
    return item_status

def extract_user_specific_feature(uid, check_date, user_items, delta):
    start_date = check_date-delta
    usf = []
    def add_feature(val):
        nonlocal usf 
        if val is not False and val == 0:
            usf.append(-1)
        else:
            usf.append(val)
    buy_days = 0
    last_buy_date = start_date-d1
    visits = 0
    marks = 0
    carts = 0
    buys = 0
    for _, iid, bt, geohash, cate, date in user_items[uid]:
        today = date.date()
        if not (start_date <= today <= check_date):
            continue
        if bt == 1:
            visits += 1
        elif bt == 2:
            marks += 1
        elif bt == 3:
            carts += 1
        else:
            buys += 1
            if last_buy_date != today:
                buy_days += 1
                last_buy_date = today
    if visits != 0:
        buy_rate = buys/visits
    else:
        buy_rate = 0

    add_feature(buy_days)
    add_feature(visits)
    add_feature(marks)
    add_feature(carts)
    add_feature(buys)
    add_feature(buy_rate)
    return usf


def extract_item_specific_feature(iid, cate, check_date, item_status, delta):
    start_date = check_date-delta
    isf = []
    def add_feature(val):
        nonlocal isf 
        if val is not False and val == 0:
            isf.append(-1)
        else:
            isf.append(val)

    cate_sell = 0
    item_sell = 0
    while start_date <= check_date:
        for _iid, btd in item_status[start_date][cate].items():
            if _iid == iid:
                item_sell += btd[4]
            cate_sell += btd[4]
        start_date += d1
    if cate_sell == 0:
        item_buy_rate = -1
    else:
        item_buy_rate = item_sell/cate_sell

    add_feature(item_sell)
    add_feature(cate_sell)
    add_feature(item_buy_rate)
    return isf

def extend_feature(feature_set, item_status, user_items, uid, delta):
    for uif in feature_set:
        iid, cate, date, *rest = uif
        isf = extract_item_specific_feature(iid, cate, date,
                                            item_status, delta)
        uif.extend(isf)
        usf = extract_user_specific_feature(uid, date, user_items, delta)
        uif.extend(usf)


def extract_user_item_feature(records, delta):
    records = records.copy()
    dates = list(set(map(lambda x: x[5].date(), records)))
    dates.sort()
    check_day = dates[0] + delta
    end = dates[-1]
    m1p = []
    m1n = []
    m2p = []
    m2n = []
    pre1_set = []
    pre2_set = []
    while check_day <= end:
        iids = set()
        for iid, cate in map(
                lambda x: [x[1], x[4]],
                filter(lambda y: y[5].date() == check_day, records)):
            if iid in iids:
                continue
            iids.add(iid)
            uifs = []
            def add_feature(val):
                nonlocal uifs
                if val is not False and val == 0:
                    uifs.append(-1)
                else:
                    uifs.append(val)
            related_records = list(filter(
                lambda x: check_day-delta <= x[5].date() <= check_day+d1,
                records))
            add_feature(iid)
            add_feature(cate)
            add_feature(check_day)

            # Actions in related records
            cates = set()
            items = set()
            key_cate_num = 0
            key_item_num = 0
            for _, _iid, bt, _, _cate, date in related_records:
                cates.add(_cate)
                items.add(_iid)
                if _iid == iid:
                    key_item_num += 1
                else:
                    pass
                if _cate == cate:
                    key_cate_num += 1
            cate_num = len(cates)
            items_num = len(items)
            add_feature(cate_num)
            add_feature(items_num)
            if key_cate_num == 0:
                add_feature(-1)
            else:
                add_feature(key_item_num/key_cate_num)

            # Actions on check day
            added_cart = False
            online = [None, None]
            time_on_item = [None, None]
            buy_on_check_day = False
            buy_after_interact = False
            for _, _iid, bt, _, _, date in filter(
                    lambda x: x[5].date() == check_day, related_records):
                if _iid == iid and bt == 3:
                    added_cart = True
                if bt == 4:
                    buy_on_check_day = True
                if added_cart is True and bt == 4:
                    buy_after_interact = True

                online[0] = min(online[0], date) if online[0] is not None\
                        else date
                online[1] = max(online[1], date) if online[1] is not None\
                        else date
                if _iid == iid:
                    time_on_item[0] = min(time_on_item[0], date) if\
                            time_on_item[0] is not None else date
                    time_on_item[1] = max(time_on_item[1], date) if\
                            time_on_item[1] is not None else date
                time_on_item[1] = min(time_on_item[1], date) if\
                        time_on_item[1] is not None and\
                        time_on_item[1] != time_on_item[0] else date
            online_time = (online[1]-online[0]).seconds/60
            interact_time = (time_on_item[1]-time_on_item[0]).seconds/60
            add_feature(online_time)
            add_feature(interact_time)
            add_feature(buy_on_check_day)
            add_feature(buy_after_interact)

            # Did buy on the day after check_day ?
            buy_on_key_day = False
            for _, _iid, bt, _, _, _ in filter(lambda x: x[1] == iid and\
                    x[5].date() == check_day+d1, related_records):
                if bt == 4:
                    buy_on_key_day = True

            if check_day < date_1217 and added_cart:
                if buy_on_key_day:
                    m1p.append(uifs)
                else:
                    m1n.append(uifs)
            elif check_day < date_1217:
                if buy_on_key_day:
                    m2p.append(uifs)
                else:
                    m2n.append(uifs)
            else:
                if buy_on_key_day:
                    pre1_set.append(uifs)
                else:
                    pre2_set.append(uifs)
        check_day += d1
    return m1p, m1n, m2p, m2n, pre1_set, pre2_set

@timeit
def generate_user_item_raltions(data_path):
    """
        user_items is a defaultdict with uid as key and record list as value.
        sort by iid and date in ascending order.
            uid -> [record_0, record_1, ...]
    """
    info('Extracting user-item relations from data_set')
    data_set, retrived = file_retrive(data_path)
    data_size = len(data_set)

    user_items = defaultdict(list)
    p = Progress(data_size)
    for record in data_set:
        p.next()
        user_items[record[0]].append(record)

    drops = []
    for uid, records in user_items.items():
        if not any(map(lambda x: x[2] == 4, user_items[uid])):
            drops.append(uid)
    drop_size = len(drops)

    for uid in drops:
        user_items.pop(uid)
    info('Drop no-buy users: %d' % drop_size)

    info('Sorting user-item relations')
    ui_size = len(user_items.keys())
    p = Progress(ui_size)
    for records in user_items.values():
        p.next()
        records.sort(key=lambda x: (x[5], x[1]))

    save_to_file(user_items, 'UIR-'+data_path)
    return user_items

@timeit
def generate_feature_set(w_size, data_path='', cache=0):
    info('generate feature set')

    if cache:
        info('Try to Load feature set from cache')
        cart_buy, r1 = file_retrive('CART_BUY-'+data_path)
        no_cart_buy, r2 = file_retrive('NO_CART_BUY-'+data_path)
        cart_no_buy, r3 = file_retrive('CART_NO_BUY-'+data_path)
        no_cart_no_buy, r4 = file_retrive('NO_CART_NO_BUY-'+data_path)
        prediction_set1, r5 = file_retrive('PREDICTION_SET1-'+data_path)
        prediction_set2, r6 = file_retrive('PREDICTION_SET2-'+data_path)
        if r1 and r2 and r3 and r4 and r5 and r6:
            info('Using feature_set cache')
            return cart_buy, no_cart_buy, cart_no_buy, no_cart_no_buy,\
                prediction_set1, prediction_set2
        else:
            info('Failed on reading cache:')
            if not r1:
                info('No cache for CART_BUY')
            if not r2:
                info('No cache for CART_NO_BUY')
            if not r3:
                info('No cache for NO_CART_BUY')
            if not r4:
                info('No cache for NO_CART_NO_BUY')
            if not r5:
                info('No cache for PREDICTION_SET')
        info('Try to Load user-item relations from cache')
        user_items, retrived = file_retrive('UIR-'+data_path)
        if not retrived:
            info('No uset_items cache')
            user_items = generate_user_item_raltions(data_path)
        else:
            info('Using uset_items cache')
    else:
        user_items = generate_user_item_raltions(data_path)

    item_status = extract_item_status(user_items)
    delta = timedelta(w_size)

    info('Extracting features')
    cart_buy = []
    no_cart_buy = []
    cart_no_buy = []
    no_cart_no_buy = []
    prediction_set1 = []
    prediction_set2 = []

    p = Progress(len(user_items.keys()))
    for uid, records in user_items.items():
        p.next()
        m1p, m1n, m2p, m2n, p1, p2 = extract_user_item_feature(records, delta)
        extend_feature(m1p, item_status, user_items, uid, delta)
        extend_feature(m1n, item_status, user_items, uid, delta)
        extend_feature(m2p, item_status, user_items, uid, delta)
        extend_feature(m2n, item_status, user_items, uid, delta)
        extend_feature(p1, item_status, user_items, uid, delta)
        extend_feature(p2, item_status, user_items, uid, delta)

        m1p = [x[3:] for x in m1p]
        m1n = [x[3:] for x in m1n]
        m2p = [x[3:] for x in m2p]
        m2n = [x[3:] for x in m2n]
        p1 = [[uid, x[0]]+x[3:] for x in p1]
        p2 = [[uid, x[0]]+x[3:] for x in p2]

        cart_buy.extend(m1p)
        cart_no_buy.extend(m1n)
        no_cart_buy.extend(m2p)
        no_cart_no_buy.extend(m2n)
        prediction_set1.extend(p1)
        prediction_set2.extend(p2)

    save_to_file(cart_buy, 'CART_BUY-'+data_path)
    save_to_file(cart_no_buy, 'CART_NO_BUY-'+data_path)
    save_to_file(no_cart_buy, 'NO_CART_BUY-'+data_path)
    save_to_file(no_cart_no_buy, 'NO_CART_NO_BUY-'+data_path)
    save_to_file(prediction_set1, 'PREDICTION_SET1-'+data_path)
    save_to_file(prediction_set2, 'PREDICTION_SET2-'+data_path)

    return cart_buy, cart_no_buy, no_cart_buy,\
        no_cart_no_buy, prediction_set1, prediction_set2


if __name__ == '__main__':
    w_size, data_path, cache = parse_args()
    generate_feature_set(w_size, data_path, cache)
