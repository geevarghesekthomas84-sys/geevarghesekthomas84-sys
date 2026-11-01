/**
 * SecurePrefsManager.kt — Android EncryptedSharedPreferences Wrapper
 * Author: Geevarghese K Thomas (@geevarghesekthomas84-sys)
 *
 * Drop-in wrapper around AndroidX EncryptedSharedPreferences with
 * type-safe get/set, automatic key generation, and a clean Kotlin API.
 *
 * Dependencies:
 *   implementation("androidx.security:security-crypto:1.1.0-alpha06")
 *
 * Usage:
 *   val prefs = SecurePrefsManager.getInstance(context)
 *   prefs.put("api_token", "sk-abc123...")
 *   val token: String? = prefs.get("api_token")
 *   prefs.put("retry_count", 3)
 *   val count: Int = prefs.get("retry_count", 0)
 */

package dev.gg.security

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey

class SecurePrefsManager private constructor(context: Context) {

    private val masterKey = MasterKey.Builder(context)
        .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
        .build()

    private val prefs: SharedPreferences = EncryptedSharedPreferences.create(
        context,
        PREFS_FILE,
        masterKey,
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM,
    )

    fun put(key: String, value: Any?) {
        prefs.edit().apply {
            when (value) {
                is String  -> putString(key, value)
                is Int     -> putInt(key, value)
                is Long    -> putLong(key, value)
                is Float   -> putFloat(key, value)
                is Boolean -> putBoolean(key, value)
                is Set<*>  -> putStringSet(key, value.filterIsInstance<String>().toSet())
                null       -> remove(key)
                else       -> throw IllegalArgumentException("Unsupported type: ${value::class}")
            }
            apply()
        }
    }

    @Suppress("UNCHECKED_CAST")
    fun <T> get(key: String, default: T? = null): T? {
        if (!prefs.contains(key)) return default
        return when (default) {
            is Int     -> prefs.getInt(key, default) as T
            is Long    -> prefs.getLong(key, default) as T
            is Float   -> prefs.getFloat(key, default) as T
            is Boolean -> prefs.getBoolean(key, default) as T
            is Set<*>  -> prefs.getStringSet(key, emptySet()) as T
            else       -> prefs.getString(key, default as? String) as T?
        }
    }

    fun remove(key: String) = prefs.edit().remove(key).apply()

    fun clear() = prefs.edit().clear().apply()

    fun contains(key: String): Boolean = prefs.contains(key)

    fun allKeys(): Set<String> = prefs.all.keys

    companion object {
        private const val PREFS_FILE = "gg_secure_prefs"

        @Volatile
        private var instance: SecurePrefsManager? = null

        fun getInstance(context: Context): SecurePrefsManager =
            instance ?: synchronized(this) {
                instance ?: SecurePrefsManager(context.applicationContext).also { instance = it }
            }
    }
}
