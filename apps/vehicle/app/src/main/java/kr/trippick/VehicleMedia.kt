package kr.trippick

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import androidx.compose.material.Text
import androidx.compose.foundation.layout.Box
import coil.compose.SubcomposeAsyncImage
import coil.request.ImageRequest
import com.google.zxing.BarcodeFormat
import com.google.zxing.qrcode.QRCodeWriter

@Composable
fun InviteQr(url: String, modifier: Modifier) {
    val bitmap =
        remember(url) {
            val code = QRCodeWriter().encode(url, BarcodeFormat.QR_CODE, 320, 320)
            val pixels =
                IntArray(320 * 320) {
                    if (code[it % 320, it / 320]) android.graphics.Color.BLACK
                    else android.graphics.Color.WHITE
                }
            Bitmap.createBitmap(pixels, 320, 320, Bitmap.Config.ARGB_8888).asImageBitmap()
        }
    Image(bitmap, "여행 QR", modifier)
}

@Composable
fun Preview(model: TravelModel, id: String, modifier: Modifier) {
    val context = LocalContext.current
    val request =
        remember(id, model.trip, model.token) {
            val key = java.security.MessageDigest.getInstance("SHA-256").digest(
                (BuildConfig.API_ORIGIN + "/" + model.trip + "/" + id + "/" + model.token).toByteArray()
            ).joinToString("") { "%02x".format(it) }
            ImageRequest.Builder(context)
                .data(
                    BuildConfig.API_ORIGIN +
                        "/api/v1/trips/" +
                        model.trip +
                        "/photos/" +
                        id +
                        "/preview"
                )
                .addHeader("Authorization", "Bearer " + model.token)
                .size(640)
                .diskCacheKey(key)
                .memoryCacheKey(key)
                .build()
        }
    SubcomposeAsyncImage(request, "여행 사진", modifier, error = {
        Box { Text("사진을 불러올 수 없음") }
    })
}
