# ── kotlinx.serialization ──
-keepattributes *Annotation*, InnerClasses
-dontnote kotlinx.serialization.AnnotationsKt
-keepclassmembers class kotlinx.serialization.json.** { *** Companion; }
-keepclasseswithmembers class kotlinx.serialization.json.** {
    kotlinx.serialization.KSerializer serializer(...);
}
-keep,includedescriptorclasses class com.makoto.android.**$$serializer { *; }
-keepclassmembers class com.makoto.android.** {
    *** Companion;
}
-keepclasseswithmembers class com.makoto.android.** {
    kotlinx.serialization.KSerializer serializer(...);
}

# ── Retrofit ──
-keepattributes Signature, InnerClasses, EnclosingMethod
-keepattributes RuntimeVisibleAnnotations, RuntimeVisibleParameterAnnotations
-keepclassmembers,allowshrinking,allowobfuscation interface * {
    @retrofit2.http.* <methods>;
}
-dontwarn javax.annotation.**
-dontwarn kotlin.Unit
-dontwarn retrofit2.KotlinExtensions
-dontwarn retrofit2.KotlinExtensions$*

# ── OkHttp ──
-dontwarn okhttp3.**
-dontwarn okio.**
-keepnames class okhttp3.internal.publicsuffix.PublicSuffixDatabase

# ── Jetpack Compose ──
-keep class androidx.compose.** { *; }
-dontwarn androidx.compose.**

# ── Lifecycle / ViewModel ──
-keep class androidx.lifecycle.** { *; }
-keep class androidx.activity.** { *; }

# ── Navigation ──
-keep class androidx.navigation.** { *; }

# ── DataStore ──
-keepclassmembers class * extends androidx.datastore.preferences.protobuf.GeneratedMessageLite {
    <fields>;
}

# ── Glance Widget ──
-keep class com.makoto.android.widget.** { *; }

# ── App entry points ──
-keep class com.makoto.android.MainActivity { *; }
-keep class com.makoto.android.MakotoApp { *; }
