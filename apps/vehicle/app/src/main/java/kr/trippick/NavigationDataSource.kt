package kr.trippick

data class NavigationObservation(val kind:String,val name:String,val latitude:Double?,val longitude:Double?,val address:String="",val simulated:Boolean=false)
interface NavigationDataSource {
    fun start()
    fun close()
}
