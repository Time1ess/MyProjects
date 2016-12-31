	record:
		[uid, iid, behavior, geohash, category, datetime]	
		
	user_items:
		uid -> [record-1, record-2, ...]
		
		* sort by [datetime, iid] in ascending order
	
	item_status:
		date -> cate -> iid -> behavior -> cnt
		
	feature:
	 	[
	1	 category_nums_interacted,
	2	 item_nums_interacted,
	3	 key_item_interacted_cnt / key_category_intercated_cnt,
	4	 online_time,
	5	 interact_time_on_key_item,
	6	 is_buy_on_check_day,
	7	 is_buy_after_interact,
	8	 key_item_sells_in_period,
	9	 key_cate_sells_in_period,
	10	 key_item_sells / key_cate_sells,
	11	 user_buy_days_in_period,
	12	 user_visits_in_period,
	13	 user_marks_in_period,
	14	 user_add_carts_in_period,
	15	 user_buys_in_period,
	16	 user_purchase_conversion_rate,
		 ]
