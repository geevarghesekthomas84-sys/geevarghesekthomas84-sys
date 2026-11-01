/**
 * NetworkSecurityHelper.kt — Android SSL Pinning & Certificate Transparency Helper
 * Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)
 *
 * Drop-in OkHttp SSL pinning configuration with certificate validation,
 * connection security logging, and helper methods for Gria-AI style apps.
 *
 * Dependencies:
 *   implementation("com.squareup.okhttp3:okhttp:4.12.0")
 *
 * Usage:
 *   val client = NetworkSecurityHelper.createSecureClient(
 *       baseUrl = "https://api.example.com",
 *       pins = listOf("sha256/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA=")
 *   )
 */

package dev.gg.security

import android.util.Log
import okhttp3.CertificatePinner
import okhttp3.ConnectionSpec
import okhttp3.Interceptor
import okhttp3.OkHttpClient
import okhttp3.TlsVersion
import okhttp3.logging.HttpLoggingInterceptor
import java.security.cert.X509Certificate
import java.util.concurrent.TimeUnit
import javax.net.ssl.SSLPeerUnverifiedException

object NetworkSecurityHelper {

    private const val TAG = "NetSec"

    fun createSecureClient(
        baseUrl: String,
        pins: List<String> = emptyList(),
        connectTimeoutSec: Long = 15,
        readTimeoutSec: Long = 30,
        enableLogging: Boolean = false,
    ): OkHttpClient {
        val hostname = extractHostname(baseUrl)
        val builder = OkHttpClient.Builder()
            .connectTimeout(connectTimeoutSec, TimeUnit.SECONDS)
            .readTimeout(readTimeoutSec, TimeUnit.SECONDS)
            .connectionSpecs(listOf(modernTlsSpec(), ConnectionSpec.CLEARTEXT))
            .addInterceptor(securityHeaderInterceptor())

        if (pins.isNotEmpty()) {
            val pinner = CertificatePinner.Builder().apply {
                pins.forEach { pin -> add(hostname, pin) }
            }.build()
            builder.certificatePinner(pinner)
            Log.d(TAG, "SSL pinning enabled for $hostname with ${pins.size} pin(s)")
        }

        if (enableLogging) {
            builder.addInterceptor(
                HttpLoggingInterceptor { msg -> Log.d(TAG, msg) }
                    .setLevel(HttpLoggingInterceptor.Level.HEADERS)
            )
        }

        builder.addNetworkInterceptor(tlsVersionLogger())

        return builder.build()
    }

    private fun modernTlsSpec(): ConnectionSpec =
        ConnectionSpec.Builder(ConnectionSpec.MODERN_TLS)
            .tlsVersions(TlsVersion.TLS_1_2, TlsVersion.TLS_1_3)
            .build()

    private fun securityHeaderInterceptor() = Interceptor { chain ->
        val request = chain.request().newBuilder()
            .header("X-Content-Type-Options", "nosniff")
            .header("X-Requested-With", "GriaAI-Android")
            .build()
        chain.proceed(request)
    }

    private fun tlsVersionLogger() = Interceptor { chain ->
        val response = chain.proceed(chain.request())
        val handshake = response.handshake
        if (handshake != null) {
            Log.d(TAG, buildString {
                append("TLS: ${handshake.tlsVersion}")
                append(" | Cipher: ${handshake.cipherSuite}")
                try {
                    val cert = handshake.peerCertificates.firstOrNull() as? X509Certificate
                    if (cert != null) {
                        append(" | CN: ${cert.subjectX500Principal.name}")
                        append(" | Expires: ${cert.notAfter}")
                    }
                } catch (e: SSLPeerUnverifiedException) {
                    append(" | Peer unverified")
                }
            })
        }
        response
    }

    private fun extractHostname(url: String): String =
        url.removePrefix("https://")
            .removePrefix("http://")
            .substringBefore("/")
            .substringBefore(":")

    fun validateCertExpiry(client: OkHttpClient, url: String): CertStatus {
        val request = okhttp3.Request.Builder().url(url).head().build()
        return try {
            client.newCall(request).execute().use { response ->
                val cert = response.handshake
                    ?.peerCertificates
                    ?.firstOrNull() as? X509Certificate

                if (cert == null) return CertStatus.Unknown

                val daysRemaining = ((cert.notAfter.time - System.currentTimeMillis()) / 86_400_000).toInt()
                when {
                    daysRemaining < 0   -> CertStatus.Expired(daysRemaining)
                    daysRemaining < 30  -> CertStatus.ExpiringSoon(daysRemaining)
                    else                -> CertStatus.Valid(daysRemaining)
                }
            }
        } catch (e: Exception) {
            Log.e(TAG, "Certificate validation failed", e)
            CertStatus.Error(e.message ?: "Unknown error")
        }
    }

    sealed class CertStatus {
        data class Valid(val daysRemaining: Int) : CertStatus()
        data class ExpiringSoon(val daysRemaining: Int) : CertStatus()
        data class Expired(val daysOverdue: Int) : CertStatus()
        data class Error(val message: String) : CertStatus()
        data object Unknown : CertStatus()
    }
}
