


@router.get("/get")
def getcities(db : Session = Depends(get_db) ,user : USER =  Depends(get_current_user)):
    return db.query(zone.name).join(flood_predection,flood_predection.zone_id == zone.id).filter(flood_predection.score_risk > 0.5).all()

     




     