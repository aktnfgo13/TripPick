package kr.trippick

import android.graphics.Bitmap
import androidx.compose.foundation.Image
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.asImageBitmap
import androidx.compose.ui.platform.LocalContext
import coil.compose.AsyncImage
import coil.request.ImageRequest
import com.google.zxing.BarcodeFormat
import com.google.zxing.qrcode.QRCodeWriter

@Composable fun InviteQr(url:String,modifier:Modifier){
    val bitmap=remember(url){
        val code=QRCodeWriter().encode(url,BarcodeFormat.QR_CODE,320,320)
        val pixels=IntArray(320*320){if(code[it%320,it/320]) android.graphics.Color.BLACK else android.graphics.Color.WHITE}
        Bitmap.createBitmap(pixels,320,320,Bitmap.Config.ARGB_8888).asImageBitmap()
    }
    Image(bitmap,"여행 QR",modifier)
}
@Composable fun Preview(model:TravelModel,id:String,modifier:Modifier){
    val context=LocalContext.current
    val request=remember(id,model.trip){
        ImageRequest.Builder(context).data(BuildConfig.API_ORIGIN+"/api/v1/trips/"+model.trip+"/photos/"+id+"/preview")
            .addHeader("Authorization","Bearer "+model.token).size(640).diskCachePolicy(coil.request.CachePolicy.DISABLED).build()
    }
    AsyncImage(request,"여행 사진",modifier)
}
