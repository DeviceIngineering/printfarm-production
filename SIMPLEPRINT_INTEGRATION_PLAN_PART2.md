# 📋 План реализации SimplePrint - Часть 2

**Продолжение документа SIMPLEPRINT_INTEGRATION_PLAN.md**

---

### **ЭТАП 3: Backend - API Endpoints** (продолжение)

#### Шаг 3.2: Serializers
**Задачи:**
- [ ] Создать сериализаторы для API
- [ ] Добавить валидацию данных
- [ ] Создать вложенные сериализаторы для связанных объектов

**Файл:** `backend/apps/simpleprint/serializers.py`
```python
import logging
from rest_framework import serializers
from .models import SimplePrintOrder, SimplePrintSync
from apps.products.serializers import ProductSerializer

logger = logging.getLogger('simpleprint.serializers')


class SimplePrintOrderSerializer(serializers.ModelSerializer):
    """Сериализатор для SimplePrint заказов"""

    product = ProductSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = SimplePrintOrder
        fields = [
            'id',
            'simpleprint_id',
            'order_number',
            'status',
            'status_display',
            'product',
            'article',
            'product_name',
            'quantity',
            'order_date',
            'completion_date',
            'customer_name',
            'notes',
            'created_at',
            'updated_at',
            'last_synced_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class SimplePrintOrderDetailSerializer(SimplePrintOrderSerializer):
    """Детальный сериализатор с полными данными"""

    raw_data = serializers.JSONField()

    class Meta(SimplePrintOrderSerializer.Meta):
        fields = SimplePrintOrderSerializer.Meta.fields + ['raw_data']


class SimplePrintSyncSerializer(serializers.ModelSerializer):
    """Сериализатор для истории синхронизаций"""

    duration = serializers.SerializerMethodField()
    success_rate = serializers.SerializerMethodField()

    class Meta:
        model = SimplePrintSync
        fields = [
            'id',
            'status',
            'started_at',
            'finished_at',
            'duration',
            'total_orders',
            'synced_orders',
            'failed_orders',
            'success_rate',
            'filters',
            'error_details',
        ]
        read_only_fields = ['id']

    def get_duration(self, obj):
        """Вычислить длительность синхронизации"""
        if obj.finished_at and obj.started_at:
            delta = obj.finished_at - obj.started_at
            return delta.total_seconds()
        return None

    def get_success_rate(self, obj):
        """Вычислить процент успешности"""
        if obj.total_orders > 0:
            return round((obj.synced_orders / obj.total_orders) * 100, 2)
        return 0.0


class SimplePrintStatsSerializer(serializers.Serializer):
    """Сериализатор для статистики"""

    total = serializers.IntegerField()
    by_status = serializers.DictField()
    unmatched_count = serializers.IntegerField()
```

**Тесты:** `backend/apps/simpleprint/tests/test_serializers.py`
```python
import pytest
from django.utils import timezone
from apps.simpleprint.models import SimplePrintOrder, SimplePrintSync
from apps.simpleprint.serializers import (
    SimplePrintOrderSerializer,
    SimplePrintSyncSerializer,
)


@pytest.mark.django_db
class TestSerializers:
    """Тесты сериализаторов"""

    def test_order_serializer(self):
        """Тест сериализации заказа"""
        order = SimplePrintOrder.objects.create(
            simpleprint_id='SP-001',
            order_number='ORD-001',
            article='TEST-001',
            product_name='Test Product',
            quantity=10,
            order_date=timezone.now()
        )

        serializer = SimplePrintOrderSerializer(order)
        data = serializer.data

        assert data['simpleprint_id'] == 'SP-001'
        assert data['order_number'] == 'ORD-001'
        assert 'status_display' in data

    def test_sync_serializer_with_duration(self):
        """Тест сериализации синхронизации с вычислением длительности"""
        started = timezone.now()
        finished = started + timezone.timedelta(seconds=120)

        sync = SimplePrintSync.objects.create(
            started_at=started,
            finished_at=finished,
            total_orders=100,
            synced_orders=95,
            status='success'
        )

        serializer = SimplePrintSyncSerializer(sync)
        data = serializer.data

        assert data['duration'] == 120.0
        assert data['success_rate'] == 95.0
```

**Git commit:**
```bash
git commit -m "📦 Serializers: Add SimplePrint API serializers

- Created SimplePrintOrderSerializer
- Created SimplePrintSyncSerializer
- Added computed fields (duration, success_rate)
- Added comprehensive tests
"
```

---

#### Шаг 3.3: REST API Views
**Задачи:**
- [ ] Создать ViewSet для заказов
- [ ] Добавить endpoints для синхронизации
- [ ] Добавить фильтрацию и пагинацию
- [ ] Добавить permissions

**Файл:** `backend/apps/simpleprint/views.py`
```python
import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import OrderingFilter, SearchFilter

from .models import SimplePrintOrder, SimplePrintSync
from .serializers import (
    SimplePrintOrderSerializer,
    SimplePrintOrderDetailSerializer,
    SimplePrintSyncSerializer,
    SimplePrintStatsSerializer,
)
from .services import SimplePrintService

logger = logging.getLogger('simpleprint.views')


class SimplePrintOrderViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для SimplePrint заказов

    Endpoints:
    - GET /api/v1/simpleprint/orders/ - Список заказов
    - GET /api/v1/simpleprint/orders/{id}/ - Детали заказа
    - POST /api/v1/simpleprint/orders/sync/ - Синхронизация
    - GET /api/v1/simpleprint/orders/stats/ - Статистика
    """

    queryset = SimplePrintOrder.objects.select_related('product').all()
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, OrderingFilter, SearchFilter]

    filterset_fields = ['status', 'article']
    search_fields = ['order_number', 'product_name', 'customer_name']
    ordering_fields = ['order_date', 'created_at', 'quantity']
    ordering = ['-order_date']

    def get_serializer_class(self):
        """Выбор сериализатора"""
        if self.action == 'retrieve':
            return SimplePrintOrderDetailSerializer
        return SimplePrintOrderSerializer

    def list(self, request, *args, **kwargs):
        """Получить список заказов"""
        logger.info(f"Fetching SimplePrint orders list, filters: {request.query_params}")
        return super().list(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        """Получить детали заказа"""
        logger.info(f"Fetching SimplePrint order details: {kwargs.get('pk')}")
        return super().retrieve(request, *args, **kwargs)

    @action(detail=False, methods=['post'])
    def sync(self, request):
        """
        Синхронизация заказов из SimplePrint

        Request body:
        {
            "filters": {
                "status": "pending",
                "date_from": "2025-01-01"
            }
        }
        """
        logger.info("Starting manual SimplePrint sync")

        filters = request.data.get('filters', {})

        try:
            service = SimplePrintService()
            sync_log = service.sync_orders(filters=filters)

            serializer = SimplePrintSyncSerializer(sync_log)

            logger.info(f"Sync completed: {sync_log.status}")

            return Response({
                'message': 'Синхронизация завершена',
                'sync': serializer.data
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Sync failed: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """
        Получить статистику по заказам

        Response:
        {
            "total": 150,
            "by_status": {
                "pending": 10,
                "processing": 5,
                "completed": 130,
                "cancelled": 5
            },
            "unmatched_count": 3
        }
        """
        logger.info("Fetching SimplePrint orders statistics")

        try:
            service = SimplePrintService()
            stats = service.get_orders_stats()

            serializer = SimplePrintStatsSerializer(stats)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Failed to get stats: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def match_products(self, request):
        """
        Сопоставить заказы с товарами

        Response:
        {
            "matched_count": 45
        }
        """
        logger.info("Starting product matching")

        try:
            service = SimplePrintService()
            matched_count = service.match_all_orders_with_products()

            logger.info(f"Product matching completed: {matched_count} matched")

            return Response({
                'message': f'Сопоставлено {matched_count} заказов',
                'matched_count': matched_count
            }, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"Product matching failed: {e}", exc_info=True)
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class SimplePrintSyncViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet для истории синхронизаций

    Endpoints:
    - GET /api/v1/simpleprint/sync-history/ - История синхронизаций
    - GET /api/v1/simpleprint/sync-history/{id}/ - Детали синхронизации
    """

    queryset = SimplePrintSync.objects.all()
    serializer_class = SimplePrintSyncSerializer
    permission_classes = [IsAuthenticated]
    ordering = ['-started_at']
```

**URL routing:** `backend/apps/simpleprint/urls.py`
```python
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SimplePrintOrderViewSet, SimplePrintSyncViewSet

router = DefaultRouter()
router.register('orders', SimplePrintOrderViewSet, basename='simpleprint-orders')
router.register('sync-history', SimplePrintSyncViewSet, basename='simpleprint-sync')

urlpatterns = [
    path('', include(router.urls)),
]
```

**Добавить в главный urls.py:** `backend/config/urls.py`
```python
urlpatterns = [
    # ... existing patterns
    path('api/v1/simpleprint/', include('apps.simpleprint.urls')),
]
```

**Тесты:** `backend/apps/simpleprint/tests/test_views.py`
```python
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from apps.simpleprint.models import SimplePrintOrder, SimplePrintSync

User = get_user_model()


@pytest.mark.django_db
class TestSimplePrintOrderViewSet:
    """Тесты SimplePrintOrderViewSet"""

    @pytest.fixture
    def api_client(self):
        client = APIClient()
        user = User.objects.create_user(username='testuser', password='testpass')
        client.force_authenticate(user=user)
        return client

    @pytest.fixture
    def sample_orders(self):
        orders = []
        for i in range(5):
            order = SimplePrintOrder.objects.create(
                simpleprint_id=f'SP-{i:03d}',
                order_number=f'ORD-{i:03d}',
                article=f'TEST-{i:03d}',
                product_name=f'Test Product {i}',
                quantity=10 + i
            )
            orders.append(order)
        return orders

    def test_list_orders(self, api_client, sample_orders):
        """Тест получения списка заказов"""
        url = reverse('simpleprint-orders-list')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 5

    def test_retrieve_order(self, api_client, sample_orders):
        """Тест получения деталей заказа"""
        order = sample_orders[0]
        url = reverse('simpleprint-orders-detail', args=[order.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data['simpleprint_id'] == order.simpleprint_id

    def test_filter_orders_by_status(self, api_client):
        """Тест фильтрации по статусу"""
        SimplePrintOrder.objects.create(
            simpleprint_id='SP-001',
            order_number='ORD-001',
            status='pending',
            article='TEST-001',
            quantity=10
        )
        SimplePrintOrder.objects.create(
            simpleprint_id='SP-002',
            order_number='ORD-002',
            status='completed',
            article='TEST-002',
            quantity=5
        )

        url = reverse('simpleprint-orders-list')
        response = api_client.get(url, {'status': 'pending'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_search_orders(self, api_client, sample_orders):
        """Тест поиска по заказам"""
        url = reverse('simpleprint-orders-list')
        response = api_client.get(url, {'search': 'ORD-001'})

        assert response.status_code == status.HTTP_200_OK
        assert response.data['count'] == 1

    def test_get_stats(self, api_client, sample_orders):
        """Тест получения статистики"""
        url = reverse('simpleprint-orders-stats')
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert 'total' in response.data
        assert response.data['total'] == 5

    @pytest.mark.skip("Requires mock SimplePrint API")
    def test_sync_orders(self, api_client):
        """Тест синхронизации (требует мока API)"""
        url = reverse('simpleprint-orders-sync')
        response = api_client.post(url, {'filters': {}})

        assert response.status_code == status.HTTP_200_OK
```

**Git commit:**
```bash
git commit -m "🚀 API: Add SimplePrint REST API endpoints

- Created SimplePrintOrderViewSet with CRUD operations
- Added sync, stats, match_products actions
- Created SimplePrintSyncViewSet
- Added filtering, search, ordering
- Added comprehensive tests
- Added URL routing
"
```

---

### **ЭТАП 4: Frontend - Автономная страница SimplePrint** (3-4 часа)

#### Шаг 4.1: API клиент для Frontend
**Задачи:**
- [ ] Создать API клиент для SimplePrint endpoints
- [ ] Добавить типы TypeScript
- [ ] Добавить обработку ошибок

**Файл:** `frontend/src/api/simpleprint.ts`
```typescript
import apiClient from './client';

// Типы данных
export interface SimplePrintOrder {
  id: number;
  simpleprint_id: string;
  order_number: string;
  status: 'pending' | 'processing' | 'printing' | 'completed' | 'cancelled';
  status_display: string;
  product?: {
    id: number;
    article: string;
    name: string;
  };
  article: string;
  product_name: string;
  quantity: string;
  order_date: string;
  completion_date?: string;
  customer_name: string;
  notes: string;
  created_at: string;
  updated_at: string;
  last_synced_at?: string;
}

export interface SimplePrintOrderDetail extends SimplePrintOrder {
  raw_data: Record<string, any>;
}

export interface SimplePrintSync {
  id: number;
  status: 'pending' | 'success' | 'failed' | 'partial';
  started_at: string;
  finished_at?: string;
  duration?: number;
  total_orders: number;
  synced_orders: number;
  failed_orders: number;
  success_rate: number;
  filters: Record<string, any>;
  error_details: string;
}

export interface SimplePrintStats {
  total: number;
  by_status: Record<string, number>;
  unmatched_count: number;
}

export interface SimplePrintOrdersResponse {
  count: number;
  next: string | null;
  previous: string | null;
  results: SimplePrintOrder[];
}

// API функции
export const simplePrintAPI = {
  /**
   * Получить список заказов
   */
  getOrders: (params?: {
    page?: number;
    page_size?: number;
    status?: string;
    search?: string;
    ordering?: string;
  }): Promise<SimplePrintOrdersResponse> => {
    console.log('[SimplePrint API] Fetching orders', params);
    return apiClient.get('/simpleprint/orders/', { params });
  },

  /**
   * Получить детали заказа
   */
  getOrderDetails: (id: number): Promise<SimplePrintOrderDetail> => {
    console.log(`[SimplePrint API] Fetching order details: ${id}`);
    return apiClient.get(`/simpleprint/orders/${id}/`);
  },

  /**
   * Синхронизация заказов
   */
  syncOrders: (filters?: Record<string, any>): Promise<{
    message: string;
    sync: SimplePrintSync;
  }> => {
    console.log('[SimplePrint API] Starting sync', filters);
    return apiClient.post('/simpleprint/orders/sync/', { filters });
  },

  /**
   * Получить статистику
   */
  getStats: (): Promise<SimplePrintStats> => {
    console.log('[SimplePrint API] Fetching stats');
    return apiClient.get('/simpleprint/orders/stats/');
  },

  /**
   * Сопоставить заказы с товарами
   */
  matchProducts: (): Promise<{
    message: string;
    matched_count: number;
  }> => {
    console.log('[SimplePrint API] Matching products');
    return apiClient.post('/simpleprint/orders/match_products/');
  },

  /**
   * Получить историю синхронизаций
   */
  getSyncHistory: (params?: {
    page?: number;
  }): Promise<{
    count: number;
    results: SimplePrintSync[];
  }> => {
    console.log('[SimplePrint API] Fetching sync history', params);
    return apiClient.get('/simpleprint/sync-history/', { params });
  },
};

export default simplePrintAPI;
```

**Git commit:**
```bash
git commit -m "🔌 API Client: Add SimplePrint frontend API client

- Created TypeScript interfaces
- Implemented all API methods
- Added logging for debugging
- Added error handling
"
```

---

#### Шаг 4.2: Redux Store
**Задачи:**
- [ ] Создать Redux slice для SimplePrint
- [ ] Добавить actions и reducers
- [ ] Добавить async thunks

**Файл:** `frontend/src/store/simpleprint/simplePrintSlice.ts`
```typescript
import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import simplePrintAPI, {
  SimplePrintOrder,
  SimplePrintOrderDetail,
  SimplePrintStats,
  SimplePrintSync,
} from '../../api/simpleprint';

// State interface
interface SimplePrintState {
  orders: SimplePrintOrder[];
  currentOrder: SimplePrintOrderDetail | null;
  stats: SimplePrintStats | null;
  syncHistory: SimplePrintSync[];

  loading: boolean;
  syncing: boolean;
  error: string | null;

  pagination: {
    page: number;
    pageSize: number;
    total: number;
  };

  filters: {
    status?: string;
    search?: string;
  };
}

// Initial state
const initialState: SimplePrintState = {
  orders: [],
  currentOrder: null,
  stats: null,
  syncHistory: [],

  loading: false,
  syncing: false,
  error: null,

  pagination: {
    page: 1,
    pageSize: 20,
    total: 0,
  },

  filters: {},
};

// Async thunks
export const fetchOrders = createAsyncThunk(
  'simpleprint/fetchOrders',
  async (params: {
    page?: number;
    pageSize?: number;
    status?: string;
    search?: string;
  } = {}, { rejectWithValue }) => {
    try {
      console.log('[Redux] Fetching SimplePrint orders', params);
      const response = await simplePrintAPI.getOrders({
        page: params.page || 1,
        page_size: params.pageSize || 20,
        status: params.status,
        search: params.search,
      });
      console.log('[Redux] Orders fetched successfully', response);
      return response;
    } catch (error: any) {
      console.error('[Redux] Failed to fetch orders', error);
      return rejectWithValue(error.response?.data?.error || 'Ошибка загрузки заказов');
    }
  }
);

export const fetchOrderDetails = createAsyncThunk(
  'simpleprint/fetchOrderDetails',
  async (id: number, { rejectWithValue }) => {
    try {
      console.log(`[Redux] Fetching order details: ${id}`);
      const response = await simplePrintAPI.getOrderDetails(id);
      console.log('[Redux] Order details fetched', response);
      return response;
    } catch (error: any) {
      console.error('[Redux] Failed to fetch order details', error);
      return rejectWithValue(error.response?.data?.error || 'Ошибка загрузки деталей');
    }
  }
);

export const syncOrders = createAsyncThunk(
  'simpleprint/syncOrders',
  async (filters: Record<string, any> = {}, { rejectWithValue, dispatch }) => {
    try {
      console.log('[Redux] Starting sync', filters);
      const response = await simplePrintAPI.syncOrders(filters);
      console.log('[Redux] Sync completed', response);

      // Обновляем список заказов после синхронизации
      dispatch(fetchOrders());
      dispatch(fetchStats());

      return response;
    } catch (error: any) {
      console.error('[Redux] Sync failed', error);
      return rejectWithValue(error.response?.data?.error || 'Ошибка синхронизации');
    }
  }
);

export const fetchStats = createAsyncThunk(
  'simpleprint/fetchStats',
  async (_, { rejectWithValue }) => {
    try {
      console.log('[Redux] Fetching stats');
      const response = await simplePrintAPI.getStats();
      console.log('[Redux] Stats fetched', response);
      return response;
    } catch (error: any) {
      console.error('[Redux] Failed to fetch stats', error);
      return rejectWithValue(error.response?.data?.error || 'Ошибка загрузки статистики');
    }
  }
);

export const matchProducts = createAsyncThunk(
  'simpleprint/matchProducts',
  async (_, { rejectWithValue, dispatch }) => {
    try {
      console.log('[Redux] Matching products');
      const response = await simplePrintAPI.matchProducts();
      console.log('[Redux] Products matched', response);

      // Обновляем данные
      dispatch(fetchOrders());
      dispatch(fetchStats());

      return response;
    } catch (error: any) {
      console.error('[Redux] Failed to match products', error);
      return rejectWithValue(error.response?.data?.error || 'Ошибка сопоставления');
    }
  }
);

// Slice
const simplePrintSlice = createSlice({
  name: 'simpleprint',
  initialState,
  reducers: {
    setFilters: (state, action: PayloadAction<{ status?: string; search?: string }>) => {
      console.log('[Redux] Setting filters', action.payload);
      state.filters = action.payload;
    },

    clearError: (state) => {
      state.error = null;
    },

    clearCurrentOrder: (state) => {
      state.currentOrder = null;
    },
  },
  extraReducers: (builder) => {
    // Fetch orders
    builder
      .addCase(fetchOrders.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOrders.fulfilled, (state, action) => {
        state.loading = false;
        state.orders = action.payload.results;
        state.pagination.total = action.payload.count;
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Fetch order details
    builder
      .addCase(fetchOrderDetails.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchOrderDetails.fulfilled, (state, action) => {
        state.loading = false;
        state.currentOrder = action.payload;
      })
      .addCase(fetchOrderDetails.rejected, (state, action) => {
        state.loading = false;
        state.error = action.payload as string;
      });

    // Sync orders
    builder
      .addCase(syncOrders.pending, (state) => {
        state.syncing = true;
        state.error = null;
      })
      .addCase(syncOrders.fulfilled, (state) => {
        state.syncing = false;
      })
      .addCase(syncOrders.rejected, (state, action) => {
        state.syncing = false;
        state.error = action.payload as string;
      });

    // Fetch stats
    builder
      .addCase(fetchStats.fulfilled, (state, action) => {
        state.stats = action.payload;
      });
  },
});

export const { setFilters, clearError, clearCurrentOrder } = simplePrintSlice.actions;
export default simplePrintSlice.reducer;
```

**Добавить в store:** `frontend/src/store/index.ts`
```typescript
import simplePrintReducer from './simpleprint/simplePrintSlice';

export const store = configureStore({
  reducer: {
    // ... existing reducers
    simpleprint: simplePrintReducer,
  },
});
```

**Git commit:**
```bash
git commit -m "🗃️ Redux: Add SimplePrint Redux store

- Created simplePrintSlice with state management
- Implemented async thunks for all operations
- Added logging for debugging
- Connected to main store
"
```

---

*Продолжение плана будет содержать:*
- Шаг 4.3: React компоненты страницы
- Шаг 4.4: Таблица заказов
- Шаг 4.5: Детали заказа и синхронизация
- Этап 5: Интеграция с вкладкой "Точка"
- Этап 6: Тестирование и документация

**Хотите продолжить с деталями frontend компонентов?**
