@file:OptIn(androidx.compose.foundation.layout.ExperimentalLayoutApi::class)

package kr.trippick

import androidx.compose.foundation.*
import androidx.compose.foundation.gestures.detectTapGestures
import androidx.compose.foundation.gestures.detectTransformGestures
import androidx.compose.foundation.layout.*
import androidx.compose.material.*
import androidx.compose.runtime.*
import androidx.compose.runtime.saveable.rememberSaveable
import androidx.compose.ui.Modifier
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.Path
import androidx.compose.ui.graphics.PathFillType
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.input.pointer.pointerInput
import androidx.compose.ui.layout.onSizeChanged
import androidx.compose.ui.unit.IntSize
import androidx.compose.ui.unit.dp
import kotlin.math.*

@Composable
internal fun Geography(
    regions: List<Region>,
    places: List<Stop>,
    detail: Boolean,
    regionClick: (String) -> Unit,
    placeClick: (String) -> Unit,
) {
    val points = remember(regions) { regions.flatMap { it.rings.flatten() } }
    val minX = points.minOf { it.x }
    val maxX = points.maxOf { it.x }
    val minY = points.minOf { it.y }
    val maxY = points.maxOf { it.y }
    var zoom by rememberSaveable { mutableFloatStateOf(1f) }
    var pan by remember { mutableStateOf(Offset.Zero) }
    var size by remember { mutableStateOf(IntSize.Zero) }
    fun scale() = min(size.width / (maxX - minX), size.height / (maxY - minY)) * .91 * zoom
    fun project(p: Point) =
        Offset(
            ((p.x - (minX + maxX) / 2) * scale() + size.width / 2).toFloat(),
            ((p.y - (minY + maxY) / 2) * scale() + size.height / 2).toFloat(),
        ) + pan
    val pins =
        if (detail) places.filter { it.region == regions[0].code && it.point != null }
        else emptyList()
    if (detail)
        FlowRow {
            TextButton(onClick = { zoom = (zoom * 1.5f).coerceAtMost(12f) }) { Text("확대") }
            TextButton(onClick = { zoom = (zoom / 1.5f).coerceAtLeast(1f) }) { Text("축소") }
        }
    Canvas(
        Modifier.fillMaxWidth()
            .height(245.dp)
            .background(Color(0xffedf6f7))
            .onSizeChanged { size = it }
            .pointerInput(detail) {
                if (detail)
                    detectTransformGestures { _, movement, factor, _ ->
                        zoom = (zoom * factor).coerceIn(1f, 12f)
                        pan += movement
                    }
            }
            .pointerInput(pins, regions, size, pan, zoom) {
                detectTapGestures { at ->
                    if (detail)
                        pins
                            .minByOrNull { (project(it.point!!) - at).getDistance() }
                            ?.takeIf { (project(it.point!!) - at).getDistance() < 40.dp.toPx() }
                            ?.let { placeClick(it.place) }
                    else
                        regions
                            .firstOrNull { r ->
                                r.rings.count { ring ->
                                    var inside = false
                                    for (i in 1 until ring.size) {
                                        val a = project(ring[i - 1])
                                        val b = project(ring[i])
                                        if (
                                            (a.y > at.y) != (b.y > at.y) &&
                                                at.x <
                                                    (b.x - a.x) * (at.y - a.y) / (b.y - a.y) + a.x
                                        )
                                            inside = !inside
                                    }
                                    inside
                                } % 2 == 1
                            }
                            ?.let { regionClick(it.code) }
                }
            }
    ) {
        for (r in regions) {
            val path = Path().apply { fillType = PathFillType.EvenOdd }
            for (ring in r.rings) {
                ring.forEachIndexed { i, p ->
                    val xy = project(p)
                    if (i == 0) path.moveTo(xy.x, xy.y) else path.lineTo(xy.x, xy.y)
                }
                path.close()
            }
            drawPath(
                path,
                if (places.any { it.region == r.code }) Color(0xff8ebda3) else Color(0xffdbe3da),
            )
            drawPath(path, Color.DarkGray, style = Stroke(1f))
        }
        for (v in pins) drawCircle(Color(0xffa53d21), 8.dp.toPx(), project(v.point!!))
    }
}
