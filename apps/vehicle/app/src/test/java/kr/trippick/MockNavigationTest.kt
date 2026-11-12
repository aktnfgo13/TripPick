package kr.trippick

import org.junit.Assert.*
import org.junit.Test

private class MockNavigationAdapter(val send:(NavigationObservation)->Unit):NavigationDataSource{
    private var running=false
    override fun start(){running=true}
    fun arrive(){if(running)send(NavigationObservation("ARRIVED","test",null,null,simulated=true))}
    override fun close(){running=false}
}

class MockNavigationTest{
    @Test fun fixturesAreExplicitAndStopAfterClose(){
        val events=mutableListOf<NavigationObservation>()
        val source=MockNavigationAdapter(events::add)
        source.start();source.arrive();source.close();source.arrive()
        assertEquals(1,events.size)
        assertTrue(events.first().simulated)
    }
}
