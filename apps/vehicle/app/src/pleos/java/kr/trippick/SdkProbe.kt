package kr.trippick
import android.content.Context
import android.util.Log
import ai.pleos.playground.vehicle.Vehicle

class SdkProbe(context: Context) {
    private val vehicle = Vehicle(context)
    private val handler=android.os.Handler(android.os.Looper.getMainLooper())
    private val probe=Runnable {
        runCatching { vehicle.getCarInfo().checkVINInfoCapabilities(
            { Log.i("TripPickSDK","CarInfo capability response available="+(it != null)) },
            { Log.w("TripPickSDK","Capability request failed",it) })
        }.onFailure { Log.w("TripPickSDK","Capability request unavailable",it) }
    }
    init {
        runCatching { vehicle.initialize(); handler.postDelayed(probe,2000L) }
            .onSuccess { Log.i("TripPickSDK","Vehicle.initialize returned") }
            .onFailure { Log.w("TripPickSDK","Vehicle initialization failed",it) }
    }
    fun close() { handler.removeCallbacks(probe);runCatching { vehicle.release() } }
}
