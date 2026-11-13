package kr.trippick

import org.junit.Assert.*
import org.junit.Test

class VehicleHomeTest {
    @Test
    fun journalRestoresOnlyVisiblePlacesInTheSavedRegion() {
        val region = Region("44", "충남", emptyList())
        val stop = Stop("visit", "place", "test", "44", null, "", "CONFIRMED", "", "MANUAL")
        val journal = Journal(listOf(region), listOf(stop), emptyMap())
        val successor = Region("12", "전남광주통합특별시", emptyList(), listOf("29", "46"))
        val updated = Journal(listOf(successor), listOf(stop.copy(region = "12")), emptyMap())
        assertEquals("12" to "place", updated.restoreRoute("29", "place"))
        assertEquals("44" to "place", journal.restoreRoute("44", "place"))
        assertEquals("44" to "", journal.restoreRoute("44", "excluded-place"))
        assertEquals("" to "", journal.restoreRoute("retired", "place"))
    }

    @Test
    fun restoreRequiresPhotoInCurrentServerListing() {
        val photos = listOf(GalleryPhoto("current", "owner", 1, true))
        assertEquals("current", restoredPhoto("current", photos))
        assertEquals("", restoredPhoto("removed", photos))
        assertEquals("", restoredPhoto("old-trip", emptyList()))
    }

    @Test
    fun votingRequiresExplicitMemberBinding() {
        assertFalse(canVote("", false))
        assertFalse(canVote("홍길동", true))
        assertTrue(canVote("홍길동", false))
    }
}
