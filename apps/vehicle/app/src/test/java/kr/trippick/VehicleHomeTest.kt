package kr.trippick

import org.junit.Assert.*
import org.junit.Test

class VehicleHomeTest {
    @Test
    fun votingRequiresExplicitMemberBinding() {
        assertFalse(canVote("", false))
        assertFalse(canVote("홍길동", true))
        assertTrue(canVote("홍길동", false))
    }
}
