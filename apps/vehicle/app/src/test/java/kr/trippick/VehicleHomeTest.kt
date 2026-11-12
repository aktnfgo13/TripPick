package kr.trippick

import org.junit.Assert.assertEquals
import org.junit.Test

class VehicleHomeTest {
    @Test fun initialScreenReportsDisconnected() {
        assertEquals("차량 서비스 미연결", VehicleHomeModel().connectionLabel)
    }
}
