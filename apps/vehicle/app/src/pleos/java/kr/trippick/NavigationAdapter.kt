package kr.trippick

import ai.pleos.playground.navi.helper.NaviHelper
import ai.pleos.playground.navi.helper.listener.NaviHelperEventListener
import ai.pleos.playground.navi.data.*
import ai.pleos.playground.navi.constants.NaviErrorCode
import android.content.Context
import android.os.Handler
import android.os.Looper
import android.util.Log

class NavigationAdapter(context:Context,private val status:(String)->Unit,private val observe:(NavigationObservation)->Unit):NavigationDataSource {
    private val helper=NaviHelper(context.applicationContext)
    private val main=Handler(Looper.getMainLooper())
    private var closed=false
    private fun report(text:String){Log.i("TripPickNavi",text);main.post { if(!closed) status(text) }}
    private fun emit(event:NavigationObservation){report(event.kind); main.post { if(!closed) observe(event) }}
    private val listener=object:NaviHelperEventListener {
        override fun onDestinationChanged(){report("DESTINATION_CHANGED");helper.getDestinationInfo()}
        override fun onDestinationInfo(info:DestinationInfo){
            emit(NavigationObservation("DESTINATION",info.name,info.latitude,info.longitude,info.address))
        }
        override fun onDestinationArrived(info:DestinationArrivedInfo){
            emit(NavigationObservation("ARRIVED",info.name,null,null,info.address))
        }
        override fun onCurrentLocationInfo(info:CurrentLocationInfo){
            emit(NavigationObservation("LOCATION",info.address,info.latitude,info.longitude,info.address))
        }
        override fun onError(errorCode:NaviErrorCode){report("NaviHelper 오류 "+errorCode)}
    }
    override fun start(){
        helper.initialize(onConnected={
            main.post { if(!closed) runCatching {
                helper.addListener(listener);report("NaviHelper 연결")
                helper.getDestinationInfo();helper.getCurrentLocationInfo()
            }.onFailure {report("내비 조회 실패")} }
        },onFailed={report("NaviHelper 연결 실패")})
    }
    override fun close(){closed=true;main.removeCallbacksAndMessages(null);runCatching{helper.removeListener(listener)};helper.release()}
}
