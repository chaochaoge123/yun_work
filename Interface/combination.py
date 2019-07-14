@login_required
@muser_required
@merchant_required
def combination_ad(request):
    """在套餐中添加商品"""
    company_id = request.company_id
    user_id = request.user_id
    no = request.params.get("no", "")
    goods_no = request.params.get('goods_no', "")

    goods_data=[]
    if not no:
        # 创建套餐
        no = common_tool.create_uuid()
        combination = DaItemCombination.objects.create(company_id=company_id, user_id=user_id, no=no)
    else:
        combination = DaItemCombination.objects.filter(no=no, company_id=company_id,
                                                       state=settings.StateEnum.VALID).first()
        if not combination.goods_data:
            return JSONResponse(error=da_settings.ERROR["NOT_EXIST_ERR"])
        _goods_data = json.loads(combination.goods_data)

    # 根据商品no,查spu_id
    goods_dict={}
    go = GoodsItem.objects.filter(no=goods_no, company_id=company_id, state=settings.StateEnum.VALID)
    for _g in go:
        spu_id = _g.spu_id
        # 型号不存在
        if spu_id not in [goods_list["spu_id"] for goods_list in _goods_data]:
            goods_dict = {"spu_id": spu_id, "count": 1, "goods": [{"using": False, "goods_no": goods_no}]}
            _goods_data.append(goods_dict)

        else:
            # 型号在，商品编号不存在
            if goods_no not in [_gl["goods_no"] for _gl in goods_list["goods"]]:
                _gl = {"using": False, "goods_no": goods_no}
                goods_list["goods"].append(_gl)
            else:
                return JSONResponse(data=["该型号的商品已存在"])

    combination.goods_data = json.dumps(_goods_data)

    combination.save()
    return JSONResponse(data=_goods_data)


@login_required
@muser_required
@merchant_required
def combination_lt(request):
    """套餐中商品列表"""
    company_id = request.company_id
    no = request.params["no"]
    combination_info = DaItemCombination.objects.filter(no=no, company_id=company_id, state=settings.StateEnum.VALID).first()
    if not combination_info:
        return JSONResponse(data={"goods_data": [], "total_price": 0})

    if combination_info .goods_data:
        goods_data=json.loads(combination_info .goods_data)

    records, noes = [], []
    total_price = 0
    for goods_list in goods_data:
        # 是否是封面
        _using = False
        for _gl in goods_list["goods"]:
            if _gl["using"]:
                _gl["using"] = False if _using else True
                _using = True
        if not _using:
            goods_list["goods"][0]["using"] = True

        noes = [_gl["goods_no"] for _gl in goods_list["goods"]][0]
        # 查商品图片,分类
        img_path = DaItem.objects.only("img_fpath","category").filter(no=noes, state=settings.StateEnum.VALID)
        for _img in img_path:
            img = _img.img_fpath
            category = _img.category
        # 查商品详情
        goods_info=GoodsItem .objects.only("name", "color", "material", "price").filter(no=noes, state=settings.StateEnum.VALID, company_id=company_id)
        for _g in goods_info:
            goods_info = {
                "name": _g.name,
                "color": _g.color,
                "color_desc": _g.get_color_display(),
                "material": _g.material,
                "material_desc": _g.get_material_display(),
                "price": _g.price,
                "color_url": storage_tool.get_absolute_url(settings.JDDA_COLOR_ICON.format(**{"color": _g.color})),
                "goods_no": noes,
                "has_item": True if noes else False ,
                "goods_path": storage_tool.get_absolute_url(img),
                "using": _using,
                "category": category,
            }

        record = {
            "spu_id": goods_list["spu_id"],
            "count": goods_list["count"],
            "goods_info": goods_info,
        }
        records .append(record)

        sup_price = goods_list["count"] * _g.price
        total_price += sup_price
    return JSONResponse(data={"combination_goods": records, "total_price": total_price})