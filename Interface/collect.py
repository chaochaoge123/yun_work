@wx_mini_required
def collect_save(request):
    u""" 上报收藏记录 """
    user_id=request.user_id
    no=request.params["no"]
    channel_type=int(request.params.get("channel",0))

    # 如果收藏的是商品
    if channel_type==0:
        info=GoodsItem.objects.only("company_id").filter(no=no).first()
        company_id=info.company_id
        Dacollect.objects.update_or_create(no=no,channel=channel_type,company_id=company_id,user_id=user_id,defaults={"modify_time": datetime.datetime.now()})
    # 如果收藏的是套装
    if channel_type==1:
        com_info=DaItemCombination.objects.only("company_id").firter(no=no).first()
        company_id=com_info.company_id
        Dacollect.objects.update_or_create(no=no, channel=channel_type, company_id=company_id, user_id=user_id,defaults={"modify_time": datetime.datetime.now()})

    return JSONResponse()


@wx_mini_required
def set_up_collect(request):
    u""" 收藏设置 """
    no = request.params["no"]
    da_collect = Dacollect.objects.filter(no=no).first()
    if not da_collect:
        return JSONResponse(error=da_settings.ERROR["NOT_EXIST_ERR"])
    if da_collect.state:
        Dacollect.objects.filter(no=no).update(state=False)
    else:
        Dacollect.objects.filter(no=no).update(state=True)

    return JSONResponse()


@wx_mini_required
def collect_list(request):
    u""" 收藏列表 """
    user_id=request.user_id
    start=int(request.params.get("start",0))
    count = int(request.params.get("count", 10))

    info=Dacollect.objects.only("channel","no").filter(user_id=user_id, state=True).order_by("-create_time")
    total_count=info.count()
    good_noes,com_noes,records_list=[],[],[]
    for _info in info[start:start+count]:

        record={
            "create_time":_info.create_time.strftime('%Y-%m-%d %H:%M:%S')
        }
        if _info.channel==settings.ChannelType.GOODS:
            good_noes.append(_info.no)

        if _info.channel == settings.ChannelType.COMBINATION:
            com_noes.append(info.no)
        records_list.append(record)

    #查套装信息：
    com_info = DaItemCombination.objects.only("name", "price", "room_type", "design_style").filter(no__in=com_noes)
    com_info_dict = {x.no: {"combination_name": x.name, "combination_price": x.price, "room_type": x.room_type,
                            "design_style": x.design_style, "room_type_desc": x.get_room_type_display(),
                            "design_style_desc": x.get_design_style_display()} for x in com_info}
    for record in records_list:
        record.update(com_info_dict.get(record["com_no"],
                                        {"combination_name": "", "combination_price": 0, "room_type": "",
                                         "design_style": "", "room_type_desc": "", "design_style_desc": ""}))

    com_img = DaItemImg.objects.only("img_fpath").filter(no__in=com_noes)
    img_dict = {_img.no: {"combination_img": storage_tool.get_absolute_url(_img.img_fpath)} for _img in com_img}
    for record in records_list:
        record.update(img_dict.get(record["com_no"], {"combination_img": ""}))

    # 商品信息
    goods_info = goods_tool.fetch_many_goods_item_detail(good_noes, settings.DA_EMPTY_IMG_FPATH)
    goods_info_dict = {
        _goods_info["goods_no"]: {
            'id': _goods_info["id"], 'name': _goods_info["name"], 'price': _goods_info["price"] / 100.0,
            'preview_url': _goods_info["preview_url"],
        } for _goods_info in goods_info}

    for _record in records_list:
        _record.update(**goods_info_dict.get(_record["item_no"], {}))

    data = {
        "start": start,
        "count": count,
        "total_count": total_count,
        "record": records_list
    }
    return JSONResponse()
