package kr.trippick
import android.content.Context

class NavigationAdapter(context:Context,val status:(String)->Unit,observe:(NavigationObservation)->Unit):NavigationDataSource {
    override fun start(){status("기본 APK · 내비 미연결")}
    override fun close(){}
}
