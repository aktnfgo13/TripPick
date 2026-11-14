package kr.trippick

import org.junit.Assert.*
import org.junit.Test

class PhoneOriginTest {
    @Test fun phoneOrigins() {
        assertTrue(validPhoneOrigin("https://trippick.test:19446"))
        listOf("http://example.com","https://127.0.0.2","https://10.0.2.2",
            "https://localhost.","https://x.localhost","https://[::1]",
            "https://secret@example.com","https://example.com/path","https://example.com#invite",
            "https://example.com?token=x").forEach { assertFalse(validPhoneOrigin(it)) }
    }
}
