package kr.trippick

import android.car.Car
import android.car.drivingstate.CarUxRestrictions
import android.car.drivingstate.CarUxRestrictionsManager
import android.content.Context
import android.util.Log

class SafetyGate(context: Context, val update: (Boolean) -> Unit) {
    private var closed = false
    private var manager: CarUxRestrictionsManager? = null

    private fun apply(rule: CarUxRestrictions?) {
        if (!closed)
            update(
                rule != null &&
                    !rule.isRequiresDistractionOptimization &&
                    rule.activeRestrictions == CarUxRestrictions.UX_RESTRICTIONS_BASELINE
            )
    }

    private val car =
        runCatching {
                Car.createCar(context, null, Car.CAR_WAIT_TIMEOUT_DO_NOT_WAIT) { car, ready ->
                    if (!closed) {
                        apply(null)
                        if (ready)
                            runCatching {
                                    manager =
                                        car.getCarManager(Car.CAR_UX_RESTRICTION_SERVICE)
                                            as CarUxRestrictionsManager
                                    manager?.registerListener(::apply)
                                    apply(manager?.currentCarUxRestrictions)
                                }
                                .onFailure { Log.w("TripPickUX", "Restrictions unavailable", it) }
                    }
                }
            }
            .getOrNull()

    fun close() {
        closed = true
        runCatching { manager?.unregisterListener() }
        car?.disconnect()
        update(false)
    }
}
