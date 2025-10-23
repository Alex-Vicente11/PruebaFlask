# Guía de Integración Android - Sistema de Usuarios Anónimos

## Tabla de Contenidos
1. [Introducción](#introducción)
2. [Configuración Inicial](#configuración-inicial)
3. [Arquitectura Recomendada](#arquitectura-recomendada)
4. [Implementación Paso a Paso](#implementación-paso-a-paso)
5. [Clases y Modelos](#clases-y-modelos)
6. [Ejemplos de Uso](#ejemplos-de-uso)
7. [Manejo de Errores](#manejo-de-errores)
8. [Testing](#testing)
9. [Mejores Prácticas](#mejores-prácticas)

---

## Introducción

Esta guía te ayudará a integrar el sistema de usuarios anónimos en tu aplicación Android. El sistema permite que los usuarios:

✅ Usen la app sin registrarse  
✅ Agreguen productos al carrito como invitados  
✅ Mantengan su carrito al registrarse o hacer login  
✅ Autenticarse con JWT tokens  

### Requisitos

- **Android SDK:** API 21+ (Android 5.0 Lollipop)
- **Kotlin:** 1.8+
- **Retrofit:** 2.9+ (para networking)
- **Gson:** 2.10+ (para JSON parsing)
- **Coroutines:** 1.7+ (para operaciones asíncronas)

---

## Configuración Inicial

### 1. Agregar Dependencias

En tu `build.gradle.kts` (Module: app):

```kotlin
dependencies {
    // Retrofit para networking
    implementation("com.squareup.retrofit2:retrofit:2.9.0")
    implementation("com.squareup.retrofit2:converter-gson:2.9.0")
    
    // OkHttp para logging y interceptors
    implementation("com.squareup.okhttp3:okhttp:4.12.0")
    implementation("com.squareup.okhttp3:logging-interceptor:4.12.0")
    
    // Coroutines
    implementation("org.jetbrains.kotlinx:kotlinx-coroutines-android:1.7.3")
    
    // ViewModel y LiveData
    implementation("androidx.lifecycle:lifecycle-viewmodel-ktx:2.7.0")
    implementation("androidx.lifecycle:lifecycle-livedata-ktx:2.7.0")
    
    // DataStore (para guardar datos de forma segura)
    implementation("androidx.datastore:datastore-preferences:1.0.0")
    
    // Optional: Encrypted SharedPreferences
    implementation("androidx.security:security-crypto:1.1.0-alpha06")
}
```

### 2. Permisos en AndroidManifest.xml

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
    
    <!-- Permisos de Internet -->
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <application
        android:usesCleartextTraffic="true"
        ...>
        ...
    </application>
</manifest>
```

⚠️ **Nota:** `usesCleartextTraffic="true"` solo para desarrollo. En producción usar HTTPS.

---

## Arquitectura Recomendada

### Estructura de Paquetes

```
com.example.app/
├── data/
│   ├── api/
│   │   ├── ApiService.kt
│   │   ├── AuthInterceptor.kt
│   │   └── RetrofitClient.kt
│   ├── model/
│   │   ├── User.kt
│   │   ├── CartItem.kt
│   │   └── ApiResponses.kt
│   ├── repository/
│   │   ├── AuthRepository.kt
│   │   └── CartRepository.kt
│   └── local/
│       └── UserPreferences.kt
├── ui/
│   ├── auth/
│   │   ├── LoginFragment.kt
│   │   ├── RegisterFragment.kt
│   │   └── AuthViewModel.kt
│   └── cart/
│       ├── CartFragment.kt
│       └── CartViewModel.kt
└── utils/
    └── Resource.kt
```

### Patrón de Arquitectura

Usaremos **MVVM (Model-View-ViewModel)** con Repository Pattern:

```
View (Fragment/Activity) → ViewModel → Repository → API Service
                              ↓
                        UserPreferences (Local Storage)
```

---

## Implementación Paso a Paso

### Paso 1: Configurar Retrofit

#### RetrofitClient.kt

```kotlin
package com.example.app.data.api

import com.google.gson.GsonBuilder
import okhttp3.OkHttpClient
import okhttp3.logging.HttpLoggingInterceptor
import retrofit2.Retrofit
import retrofit2.converter.gson.GsonConverterFactory
import java.util.concurrent.TimeUnit

object RetrofitClient {
    
    // Cambiar a la URL de producción cuando esté lista
    private const val BASE_URL = "http://192.168.68.101:5002/"
    
    private val loggingInterceptor = HttpLoggingInterceptor().apply {
        level = HttpLoggingInterceptor.Level.BODY
    }
    
    private val okHttpClient = OkHttpClient.Builder()
        .addInterceptor(loggingInterceptor)
        .addInterceptor(AuthInterceptor()) // Para agregar token automáticamente
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()
    
    private val gson = GsonBuilder()
        .setLenient()
        .create()
    
    val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(BASE_URL)
            .client(okHttpClient)
            .addConverterFactory(GsonConverterFactory.create(gson))
            .build()
    }
    
    val apiService: ApiService by lazy {
        retrofit.create(ApiService::class.java)
    }
}
```

#### AuthInterceptor.kt

```kotlin
package com.example.app.data.api

import com.example.app.data.local.UserPreferences
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.runBlocking
import okhttp3.Interceptor
import okhttp3.Response

class AuthInterceptor : Interceptor {
    
    override fun intercept(chain: Interceptor.Chain): Response {
        val request = chain.request()
        
        // Obtener token de SharedPreferences
        val token = runBlocking {
            UserPreferences.getAuthToken()
        }
        
        // Si hay token, agregarlo al header
        val newRequest = if (!token.isNullOrEmpty()) {
            request.newBuilder()
                .addHeader("Authorization", "Bearer $token")
                .build()
        } else {
            request
        }
        
        return chain.proceed(newRequest)
    }
}
```

### Paso 2: Definir Modelos de Datos

#### ApiResponses.kt

```kotlin
package com.example.app.data.model

import com.google.gson.annotations.SerializedName

// Request Models
data class GuestCreateRequest(
    @SerializedName("guest_id")
    val guestId: String
)

data class RegisterRequest(
    val email: String,
    val password: String,
    @SerializedName("user_name")
    val userName: String,
    @SerializedName("guest_id")
    val guestId: String?
)

data class LoginRequest(
    val email: String,
    val password: String,
    @SerializedName("guest_id")
    val guestId: String?
)

data class AddToCartRequest(
    @SerializedName("id_user")
    val idUser: Int,
    @SerializedName("id_product")
    val idProduct: Int,
    val quantity: Int
)

data class MergeCartRequest(
    @SerializedName("guest_id")
    val guestId: String
)

// Response Models
data class GuestCreateResponse(
    val success: Boolean,
    @SerializedName("user_id")
    val userId: Int,
    @SerializedName("is_guest")
    val isGuest: Boolean,
    val message: String
)

data class AuthResponse(
    val success: Boolean,
    @SerializedName("user_id")
    val userId: Int?,
    @SerializedName("user_name")
    val userName: String?,
    val email: String?,
    @SerializedName("is_guest")
    val isGuest: Boolean,
    val token: String?,
    @SerializedName("cart_migrated")
    val cartMigrated: Boolean,
    @SerializedName("cart_items_count")
    val cartItemsCount: Int,
    val message: String
)

data class CartResponse(
    val success: Boolean,
    @SerializedName("cartItemId")
    val cartItemId: Int?,
    val message: String
)

data class MergeCartResponse(
    val success: Boolean,
    @SerializedName("merged_items")
    val mergedItems: Int,
    val message: String
)

data class ErrorResponse(
    val success: Boolean,
    val message: String
)
```

#### User.kt

```kotlin
package com.example.app.data.model

data class User(
    val userId: Int,
    val userName: String,
    val email: String?,
    val isGuest: Boolean,
    val token: String?
)
```

### Paso 3: Crear API Service

#### ApiService.kt

```kotlin
package com.example.app.data.api

import com.example.app.data.model.*
import retrofit2.Response
import retrofit2.http.*

interface ApiService {
    
    // Guest User Endpoints
    @POST("api/guest/create")
    suspend fun createGuest(
        @Body request: GuestCreateRequest
    ): Response<GuestCreateResponse>
    
    // Authentication Endpoints
    @POST("api/auth/register")
    suspend fun register(
        @Body request: RegisterRequest
    ): Response<AuthResponse>
    
    @POST("api/auth/login")
    suspend fun login(
        @Body request: LoginRequest
    ): Response<AuthResponse>
    
    // Cart Endpoints
    @POST("add-to-cart")
    suspend fun addToCart(
        @Body request: AddToCartRequest
    ): Response<CartResponse>
    
    @POST("api/cart/merge")
    suspend fun mergeCart(
        @Body request: MergeCartRequest
    ): Response<MergeCartResponse>
    
    @GET("cart/user/{userId}")
    suspend fun getCartItems(
        @Path("userId") userId: Int
    ): Response<List<CartItem>>
    
    // Guest Cleanup (Admin)
    @DELETE("api/guest/cleanup")
    suspend fun cleanupGuests(): Response<ErrorResponse>
}

// Cart Item Model
data class CartItem(
    val product: Product,
    val quantity: Int,
    val addedDate: String
)

data class Product(
    @SerializedName("id_product")
    val idProduct: Int,
    val product: String,
    val price: Double
)
```

### Paso 4: Configurar Almacenamiento Local

#### UserPreferences.kt

```kotlin
package com.example.app.data.local

import android.content.Context
import android.content.SharedPreferences
import androidx.security.crypto.EncryptedSharedPreferences
import androidx.security.crypto.MasterKey
import java.util.UUID

object UserPreferences {
    
    private const val PREFS_NAME = "user_prefs"
    private const val KEY_USER_ID = "user_id"
    private const val KEY_USER_NAME = "user_name"
    private const val KEY_EMAIL = "email"
    private const val KEY_AUTH_TOKEN = "auth_token"
    private const val KEY_GUEST_ID = "guest_id"
    private const val KEY_IS_GUEST = "is_guest"
    
    private lateinit var prefs: SharedPreferences
    
    fun init(context: Context) {
        // Usar EncryptedSharedPreferences para mayor seguridad
        val masterKey = MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build()
        
        prefs = EncryptedSharedPreferences.create(
            context,
            PREFS_NAME,
            masterKey,
            EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
            EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
        )
    }
    
    // Guest ID Management
    fun getOrCreateGuestId(): String {
        var guestId = prefs.getString(KEY_GUEST_ID, null)
        
        if (guestId == null) {
            guestId = "guest_${UUID.randomUUID()}_${System.currentTimeMillis()}"
            prefs.edit().putString(KEY_GUEST_ID, guestId).apply()
        }
        
        return guestId
    }
    
    fun clearGuestId() {
        prefs.edit().remove(KEY_GUEST_ID).apply()
    }
    
    // User Data
    fun saveUser(user: User) {
        prefs.edit().apply {
            putInt(KEY_USER_ID, user.userId)
            putString(KEY_USER_NAME, user.userName)
            putString(KEY_EMAIL, user.email)
            putString(KEY_AUTH_TOKEN, user.token)
            putBoolean(KEY_IS_GUEST, user.isGuest)
            apply()
        }
        
        // Limpiar guest_id si ya no es guest
        if (!user.isGuest) {
            clearGuestId()
        }
    }
    
    fun getUserId(): Int {
        return prefs.getInt(KEY_USER_ID, 0)
    }
    
    fun getUserName(): String? {
        return prefs.getString(KEY_USER_NAME, null)
    }
    
    fun getEmail(): String? {
        return prefs.getString(KEY_EMAIL, null)
    }
    
    fun getAuthToken(): String? {
        return prefs.getString(KEY_AUTH_TOKEN, null)
    }
    
    fun isGuest(): Boolean {
        return prefs.getBoolean(KEY_IS_GUEST, true)
    }
    
    fun isLoggedIn(): Boolean {
        return getUserId() > 0
    }
    
    fun clearUser() {
        prefs.edit().clear().apply()
    }
}
```

### Paso 5: Crear Repository

#### AuthRepository.kt

```kotlin
package com.example.app.data.repository

import com.example.app.data.api.RetrofitClient
import com.example.app.data.local.UserPreferences
import com.example.app.data.model.*
import com.example.app.utils.Resource
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import retrofit2.Response

class AuthRepository {
    
    private val apiService = RetrofitClient.apiService
    
    suspend fun createGuestUser(): Resource<GuestCreateResponse> {
        return withContext(Dispatchers.IO) {
            try {
                val guestId = UserPreferences.getOrCreateGuestId()
                val request = GuestCreateRequest(guestId)
                
                val response = apiService.createGuest(request)
                
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    
                    // Guardar user_id del guest
                    UserPreferences.saveUser(User(
                        userId = body.userId,
                        userName = "Guest User",
                        email = null,
                        isGuest = true,
                        token = null
                    ))
                    
                    Resource.Success(body)
                } else {
                    Resource.Error("Error creating guest: ${response.code()}")
                }
            } catch (e: Exception) {
                Resource.Error("Network error: ${e.localizedMessage}")
            }
        }
    }
    
    suspend fun register(
        email: String,
        password: String,
        userName: String
    ): Resource<AuthResponse> {
        return withContext(Dispatchers.IO) {
            try {
                // Obtener guest_id si existe
                val guestId = UserPreferences.prefs.getString(
                    UserPreferences.KEY_GUEST_ID, 
                    null
                )
                
                val request = RegisterRequest(
                    email = email,
                    password = password,
                    userName = userName,
                    guestId = guestId
                )
                
                val response = apiService.register(request)
                
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    
                    if (body.success && body.token != null) {
                        // Guardar usuario autenticado
                        UserPreferences.saveUser(User(
                            userId = body.userId ?: 0,
                            userName = body.userName ?: userName,
                            email = email,
                            isGuest = false,
                            token = body.token
                        ))
                        
                        Resource.Success(body)
                    } else {
                        Resource.Error(body.message)
                    }
                } else {
                    val errorBody = response.errorBody()?.string()
                    Resource.Error("Registration failed: $errorBody")
                }
            } catch (e: Exception) {
                Resource.Error("Network error: ${e.localizedMessage}")
            }
        }
    }
    
    suspend fun login(
        email: String,
        password: String
    ): Resource<AuthResponse> {
        return withContext(Dispatchers.IO) {
            try {
                val guestId = UserPreferences.prefs.getString(
                    UserPreferences.KEY_GUEST_ID, 
                    null
                )
                
                val request = LoginRequest(
                    email = email,
                    password = password,
                    guestId = guestId
                )
                
                val response = apiService.login(request)
                
                if (response.isSuccessful && response.body() != null) {
                    val body = response.body()!!
                    
                    if (body.success && body.token != null) {
                        UserPreferences.saveUser(User(
                            userId = body.userId ?: 0,
                            userName = body.userName ?: "",
                            email = body.email,
                            isGuest = false,
                            token = body.token
                        ))
                        
                        Resource.Success(body)
                    } else {
                        Resource.Error(body.message)
                    }
                } else {
                    Resource.Error("Login failed")
                }
            } catch (e: Exception) {
                Resource.Error("Network error: ${e.localizedMessage}")
            }
        }
    }
    
    fun logout() {
        UserPreferences.clearUser()
    }
}
```

### Paso 6: Crear Clase Resource (para manejo de estados)

#### Resource.kt

```kotlin
package com.example.app.utils

sealed class Resource<T>(
    val data: T? = null,
    val message: String? = null
) {
    class Success<T>(data: T) : Resource<T>(data)
    class Error<T>(message: String, data: T? = null) : Resource<T>(data, message)
    class Loading<T> : Resource<T>()
}
```

### Paso 7: Crear ViewModel

#### AuthViewModel.kt

```kotlin
package com.example.app.ui.auth

import androidx.lifecycle.LiveData
import androidx.lifecycle.MutableLiveData
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.example.app.data.model.AuthResponse
import com.example.app.data.repository.AuthRepository
import com.example.app.utils.Resource
import kotlinx.coroutines.launch

class AuthViewModel : ViewModel() {
    
    private val repository = AuthRepository()
    
    private val _registerState = MutableLiveData<Resource<AuthResponse>>()
    val registerState: LiveData<Resource<AuthResponse>> = _registerState
    
    private val _loginState = MutableLiveData<Resource<AuthResponse>>()
    val loginState: LiveData<Resource<AuthResponse>> = _loginState
    
    fun register(email: String, password: String, userName: String) {
        _registerState.value = Resource.Loading()
        
        viewModelScope.launch {
            val result = repository.register(email, password, userName)
            _registerState.postValue(result)
        }
    }
    
    fun login(email: String, password: String) {
        _loginState.value = Resource.Loading()
        
        viewModelScope.launch {
            val result = repository.login(email, password)
            _loginState.postValue(result)
        }
    }
    
    fun logout() {
        repository.logout()
    }
}
```

---

## Ejemplos de Uso

### Ejemplo 1: Inicializar App (Crear Guest)

```kotlin
class MainActivity : AppCompatActivity() {
    
    private val authRepository = AuthRepository()
    
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Inicializar UserPreferences
        UserPreferences.init(this)
        
        // Verificar si el usuario ya está logueado
        if (!UserPreferences.isLoggedIn()) {
            // Crear usuario guest automáticamente
            lifecycleScope.launch {
                val result = authRepository.createGuestUser()
                
                when (result) {
                    is Resource.Success -> {
                        Log.d("MainActivity", "Guest created: ${result.data?.userId}")
                        // Navegar a la pantalla principal
                        navigateToHome()
                    }
                    is Resource.Error -> {
                        Log.e("MainActivity", "Error creating guest: ${result.message}")
                        showError(result.message)
                    }
                    is Resource.Loading -> {}
                }
            }
        } else {
            // Usuario ya está logueado
            navigateToHome()
        }
    }
}
```

### Ejemplo 2: Fragment de Registro

```kotlin
class RegisterFragment : Fragment() {
    
    private val viewModel: AuthViewModel by viewModels()
    private lateinit var binding: FragmentRegisterBinding
    
    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        
        setupObservers()
        setupClickListeners()
    }
    
    private fun setupObservers() {
        viewModel.registerState.observe(viewLifecycleOwner) { resource ->
            when (resource) {
                is Resource.Loading -> {
                    showLoading(true)
                }
                is Resource.Success -> {
                    showLoading(false)
                    val data = resource.data
                    
                    if (data?.cartMigrated == true) {
                        Toast.makeText(
                            requireContext(),
                            "Carrito fusionado: ${data.cartItemsCount} items",
                            Toast.LENGTH_LONG
                        ).show()
                    }
                    
                    // Navegar a la pantalla principal
                    findNavController().navigate(R.id.action_register_to_home)
                }
                is Resource.Error -> {
                    showLoading(false)
                    showError(resource.message)
                }
            }
        }
    }
    
    private fun setupClickListeners() {
        binding.btnRegister.setOnClickListener {
            val email = binding.etEmail.text.toString()
            val password = binding.etPassword.text.toString()
            val userName = binding.etUserName.text.toString()
            
            if (validateInput(email, password, userName)) {
                viewModel.register(email, password, userName)
            }
        }
    }
    
    private fun validateInput(
        email: String,
        password: String,
        userName: String
    ): Boolean {
        // Validaciones
        if (email.isBlank()) {
            binding.tilEmail.error = "Email requerido"
            return false
        }
        
        if (!android.util.Patterns.EMAIL_ADDRESS.matcher(email).matches()) {
            binding.tilEmail.error = "Email inválido"
            return false
        }
        
        if (password.length < 8) {
            binding.tilPassword.error = "La contraseña debe tener al menos 8 caracteres"
            return false
        }
        
        if (userName.isBlank()) {
            binding.tilUserName.error = "Nombre requerido"
            return false
        }
        
        return true
    }
    
    private fun showLoading(isLoading: Boolean) {
        binding.progressBar.isVisible = isLoading
        binding.btnRegister.isEnabled = !isLoading
    }
    
    private fun showError(message: String?) {
        Toast.makeText(requireContext(), message ?: "Error desconocido", Toast.LENGTH_LONG).show()
    }
}
```

### Ejemplo 3: Agregar Producto al Carrito

```kotlin
class CartRepository {
    
    private val apiService = RetrofitClient.apiService
    
    suspend fun addToCart(
        productId: Int,
        quantity: Int
    ): Resource<CartResponse> {
        return withContext(Dispatchers.IO) {
            try {
                val userId = UserPreferences.getUserId()
                
                if (userId == 0) {
                    return@withContext Resource.Error("User not found")
                }
                
                val request = AddToCartRequest(
                    idUser = userId,
                    idProduct = productId,
                    quantity = quantity
                )
                
                val response = apiService.addToCart(request)
                
                if (response.isSuccessful && response.body() != null) {
                    Resource.Success(response.body()!!)
                } else {
                    Resource.Error("Error adding to cart")
                }
            } catch (e: Exception) {
                Resource.Error("Network error: ${e.localizedMessage}")
            }
        }
    }
}
```

---

## Manejo de Errores

### Estrategia de Reintentos

```kotlin
class RetryPolicy {
    
    companion object {
        private const val MAX_RETRIES = 3
        private const val INITIAL_BACKOFF_MS = 1000L
        
        suspend fun <T> executeWithRetry(
            action: suspend () -> Resource<T>
        ): Resource<T> {
            var currentDelay = INITIAL_BACKOFF_MS
            var lastException: Exception? = null
            
            repeat(MAX_RETRIES) { attempt ->
                try {
                    val result = action()
                    
                    if (result is Resource.Success) {
                        return result
                    } else if (result is Resource.Error && attempt < MAX_RETRIES - 1) {
                        // Si es error de servidor (500), reintentar
                        if (result.message?.contains("500") == true) {
                            delay(currentDelay)
                            currentDelay *= 2 // Backoff exponencial
                        } else {
                            // Otros errores, no reintentar
                            return result
                        }
                    } else {
                        return result
                    }
                } catch (e: Exception) {
                    lastException = e
                    if (attempt < MAX_RETRIES - 1) {
                        delay(currentDelay)
                        currentDelay *= 2
                    }
                }
            }
            
            return Resource.Error(
                lastException?.localizedMessage ?: "Unknown error after retries"
            )
        }
    }
}

// Uso:
val result = RetryPolicy.executeWithRetry {
    repository.register(email, password, userName)
}
```

### Manejo de Errores de Red

```kotlin
class NetworkErrorHandler {
    
    fun handleError(exception: Exception): String {
        return when (exception) {
            is java.net.UnknownHostException -> 
                "No hay conexión a internet. Verifica tu conexión."
            
            is java.net.SocketTimeoutException -> 
                "La solicitud tardó demasiado. Intenta de nuevo."
            
            is java.net.ConnectException -> 
                "No se pudo conectar al servidor. Intenta más tarde."
            
            is retrofit2.HttpException -> {
                when (exception.code()) {
                    400 -> "Datos inválidos. Verifica la información."
                    401 -> "No autorizado. Inicia sesión nuevamente."
                    403 -> "Acceso denegado."
                    404 -> "Recurso no encontrado."
                    409 -> "El email ya está registrado."
                    500 -> "Error del servidor. Intenta más tarde."
                    else -> "Error desconocido (${exception.code()})"
                }
            }
            
            else -> exception.localizedMessage ?: "Error desconocido"
        }
    }
}
```

---

## Testing

### Test Unitario de AuthRepository

```kotlin
class AuthRepositoryTest {
    
    private lateinit var repository: AuthRepository
    private lateinit var mockApiService: ApiService
    
    @Before
    fun setup() {
        mockApiService = mock()
        repository = AuthRepository(mockApiService)
    }
    
    @Test
    fun `register success returns user with token`() = runTest {
        // Given
        val email = "test@example.com"
        val password = "password123"
        val userName = "Test User"
        
        val mockResponse = AuthResponse(
            success = true,
            userId = 15,
            userName = userName,
            email = email,
            isGuest = false,
            token = "mock_token",
            cartMigrated = true,
            cartItemsCount = 3,
            message = "Success"
        )
        
        whenever(mockApiService.register(any())).thenReturn(
            Response.success(mockResponse)
        )
        
        // When
        val result = repository.register(email, password, userName)
        
        // Then
        assertTrue(result is Resource.Success)
        assertEquals(mockResponse, (result as Resource.Success).data)
    }
    
    @Test
    fun `register with invalid email returns error`() = runTest {
        // Given
        val email = "invalid_email"
        val password = "password123"
        val userName = "Test User"
        
        val errorResponse = AuthResponse(
            success = false,
            userId = null,
            userName = null,
            email = null,
            isGuest = false,
            token = null,
            cartMigrated = false,
            cartItemsCount = 0,
            message = "Invalid email format"
        )
        
        whenever(mockApiService.register(any())).thenReturn(
            Response.success(errorResponse)
        )
        
        // When
        val result = repository.register(email, password, userName)
        
        // Then
        assertTrue(result is Resource.Error)
        assertEquals("Invalid email format", (result as Resource.Error).message)
    }
}
```

---

## Mejores Prácticas

### 1. Seguridad

✅ **DO:**
- Usar HTTPS en producción
- Almacenar tokens en EncryptedSharedPreferences
- Validar certificados SSL
- Implementar certificate pinning
- No loggear información sensible

❌ **DON'T:**
- Guardar contraseñas en texto plano
- Usar HTTP en producción
- Enviar contraseñas en logs
- Compartir tokens entre usuarios

### 2. Performance

✅ **DO:**
- Usar Coroutines para operaciones de red
- Implementar caché para datos frecuentes
- Lazy initialization de Retrofit
- Timeout razonable (30 segundos)
- Comprimir requests/responses con GZIP

### 3. User Experience

✅ **DO:**
- Mostrar loading states
- Mensajes de error claros
- Guardar estado al rotar pantalla
- Permitir pull-to-refresh
- Modo offline con caché

### 4. Arquitectura

✅ **DO:**
- Separar responsabilidades (MVVM)
- Single source of truth (Repository)
- Dependency Injection (Hilt/Koin)
- Testeable code
- Manejo centralizado de errores

---

## Checklist de Integración

- [ ] Agregar dependencias en build.gradle
- [ ] Configurar permisos de Internet
- [ ] Crear RetrofitClient y ApiService
- [ ] Implementar UserPreferences con EncryptedSharedPreferences
- [ ] Crear modelos de Request/Response
- [ ] Implementar AuthRepository
- [ ] Crear AuthViewModel
- [ ] Implementar UI de Login/Register
- [ ] Probar flujo completo: Guest → Register → Cart Merge
- [ ] Probar flujo de Login con cart merge
- [ ] Implementar manejo de errores
- [ ] Agregar tests unitarios
- [ ] Configurar ProGuard/R8 rules
- [ ] Testing en dispositivos reales
- [ ] Cambiar a URL de producción

---

## Recursos Adicionales

- [Documentación de API](API_DOCUMENTATION.md)
- [Retrofit Documentation](https://square.github.io/retrofit/)
- [Kotlin Coroutines Guide](https://kotlinlang.org/docs/coroutines-guide.html)
- [EncryptedSharedPreferences](https://developer.android.com/reference/androidx/security/crypto/EncryptedSharedPreferences)

---

**Versión:** 1.0  
**Última actualización:** 2025-10-23
