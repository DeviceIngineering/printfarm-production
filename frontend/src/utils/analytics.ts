/**
 * Система аналитики для фокус-группы PrintFarm
 * Собирает метрики пользовательского опыта и A/B тестов
 */

interface PerformanceMetrics {
  loadTime: number;
  domContentLoaded: number;
  firstContentfulPaint: number;
  largestContentfulPaint: number;
  cumulativeLayoutShift: number;
  firstInputDelay: number;
}

interface UserInteraction {
  userId: string;
  sessionId: string;
  eventType: string;
  element: string;
  page: string;
  timestamp: number;
  duration?: number;
  success?: boolean;
  errorMessage?: string;
  abVariant?: string;
}

interface FeatureUsage {
  featureName: string;
  action: string;
  userId: string;
  sessionId: string;
  duration: number;
  success: boolean;
  metadata?: Record<string, any>;
}

class AnalyticsManager {
  private userId: string;
  private sessionId: string;
  private isEnabled: boolean;
  private apiUrl: string;
  private authToken: string;
  private eventQueue: UserInteraction[] = [];
  private performanceMetrics: Partial<PerformanceMetrics> = {};
  private pageStartTime: number = Date.now();
  private interactions: Map<string, number> = new Map();

  constructor() {
    this.userId = this.getUserId();
    this.sessionId = this.generateSessionId();
    this.isEnabled = process.env.REACT_APP_ANALYTICS_ENABLED === 'true';
    this.apiUrl = process.env.REACT_APP_API_URL || '/api/v1';
    this.authToken = localStorage.getItem('auth_token') || '';
    
    this.initializeTracking();
    this.setupPerformanceTracking();
    this.setupEventListeners();
  }

  private getUserId(): string {
    let userId = localStorage.getItem('analytics_user_id');
    if (!userId) {
      userId = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('analytics_user_id', userId);
    }
    return userId;
  }

  private generateSessionId(): string {
    return 'session_' + Date.now().toString(36) + '_' + Math.random().toString(36).substr(2, 5);
  }

  private initializeTracking(): void {
    if (!this.isEnabled) return;

    // Отправка событий каждые 30 секунд
    setInterval(() => {
      this.flushEventQueue();
    }, 30000);

    // Отправка при закрытии страницы
    window.addEventListener('beforeunload', () => {
      this.flushEventQueue(true);
    });

    // Отправка при потере фокуса
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.flushEventQueue();
      }
    });
  }

  private setupPerformanceTracking(): void {
    if (!this.isEnabled || typeof window === 'undefined') return;

    // Упрощенные Performance Timing API
    window.addEventListener('load', () => {
      setTimeout(() => {
        try {
          const navigation = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming;
          
          this.performanceMetrics = {
            loadTime: navigation.loadEventEnd - navigation.loadEventStart,
            domContentLoaded: navigation.domContentLoadedEventEnd - navigation.domContentLoadedEventStart,
            firstContentfulPaint: this.getFirstContentfulPaint(),
            largestContentfulPaint: 0, // Placeholder
            cumulativeLayoutShift: 0, // Placeholder
            firstInputDelay: 0 // Placeholder
          };

          this.trackEvent('performance', 'page_load', {
            metrics: this.performanceMetrics,
            url: window.location.href,
            userAgent: navigator.userAgent,
            viewportSize: `${window.innerWidth}x${window.innerHeight}`,
            connectionType: this.getConnectionType()
          });
        } catch (error) {
          console.warn('Performance tracking error:', error);
        }
      }, 1000);
    });
  }

  private getFirstContentfulPaint(): number {
    const fcpEntry = performance.getEntriesByName('first-contentful-paint')[0];
    return fcpEntry ? fcpEntry.startTime : 0;
  }

  private getConnectionType(): string {
    const connection = (navigator as any).connection || (navigator as any).mozConnection || (navigator as any).webkitConnection;
    return connection ? connection.effectiveType || 'unknown' : 'unknown';
  }

  private setupEventListeners(): void {
    if (!this.isEnabled) return;

    // Отслеживание кликов
    document.addEventListener('click', (event) => {
      const target = event.target as HTMLElement;
      const elementInfo = this.getElementInfo(target);
      
      this.trackEvent('interaction', 'click', {
        element: elementInfo,
        coordinates: { x: event.clientX, y: event.clientY }
      });
    });

    // Отслеживание скроллинга
    let scrollTimeout: NodeJS.Timeout;
    window.addEventListener('scroll', () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(() => {
        this.trackEvent('interaction', 'scroll', {
          scrollTop: window.pageYOffset,
          scrollHeight: document.documentElement.scrollHeight,
          viewportHeight: window.innerHeight,
          scrollPercentage: Math.round((window.pageYOffset / (document.documentElement.scrollHeight - window.innerHeight)) * 100)
        });
      }, 250);
    });

    // Отслеживание времени на странице
    let timeOnPage = 0;
    setInterval(() => {
      timeOnPage += 10;
      if (timeOnPage % 60 === 0) { // Каждую минуту
        this.trackEvent('engagement', 'time_on_page', {
          timeSeconds: timeOnPage,
          page: window.location.pathname
        });
      }
    }, 10000);
  }

  private getElementInfo(element: HTMLElement): any {
    return {
      tagName: element.tagName,
      id: element.id,
      className: element.className,
      textContent: element.textContent?.substring(0, 100),
      attributes: {
        'data-testid': element.getAttribute('data-testid'),
        'aria-label': element.getAttribute('aria-label'),
        'title': element.getAttribute('title')
      }
    };
  }

  // Публичные методы для трекинга

  public trackEvent(category: string, action: string, metadata?: Record<string, any>): void {
    if (!this.isEnabled) return;

    const event: UserInteraction = {
      userId: this.userId,
      sessionId: this.sessionId,
      eventType: category,
      element: action,
      page: window.location.pathname,
      timestamp: Date.now(),
      success: true,
      abVariant: this.getCurrentABVariant(),
      ...metadata
    };

    this.eventQueue.push(event);
  }

  public trackFeatureUsage(featureName: string, action: string, success: boolean = true, metadata?: Record<string, any>): void {
    if (!this.isEnabled) return;

    const interactionKey = `${featureName}_${action}`;
    const startTime = this.interactions.get(interactionKey) || Date.now();
    const duration = Date.now() - startTime;

    const usage: FeatureUsage = {
      featureName,
      action,
      userId: this.userId,
      sessionId: this.sessionId,
      duration,
      success,
      metadata: {
        ...metadata,
        timestamp: Date.now(),
        page: window.location.pathname,
        abVariant: this.getCurrentABVariant()
      }
    };

    this.sendFeatureUsage(usage);
    this.interactions.delete(interactionKey);
  }

  public startFeatureInteraction(featureName: string, action: string): void {
    if (!this.isEnabled) return;
    
    const interactionKey = `${featureName}_${action}`;
    this.interactions.set(interactionKey, Date.now());
  }

  public trackError(error: Error, context?: Record<string, any>): void {
    if (!this.isEnabled) return;

    this.trackEvent('error', 'javascript_error', {
      errorMessage: error.message,
      errorStack: error.stack,
      context,
      userAgent: navigator.userAgent,
      url: window.location.href
    });
  }

  public trackPageView(pageName: string, additionalData?: Record<string, any>): void {
    if (!this.isEnabled) return;

    this.pageStartTime = Date.now();
    
    this.trackEvent('navigation', 'page_view', {
      pageName,
      url: window.location.href,
      referrer: document.referrer,
      timestamp: this.pageStartTime,
      ...additionalData
    });
  }

  public trackABTest(testName: string, variant: string, converted?: boolean): void {
    if (!this.isEnabled) return;

    this.trackEvent('ab_test', testName, {
      variant,
      converted: converted || false,
      timestamp: Date.now()
    });
  }

  public trackConversion(conversionType: string, value?: number, metadata?: Record<string, any>): void {
    if (!this.isEnabled) return;

    this.trackEvent('conversion', conversionType, {
      value,
      ...metadata,
      timestamp: Date.now()
    });
  }

  public trackFormInteraction(formName: string, fieldName: string, action: string): void {
    if (!this.isEnabled) return;

    this.trackEvent('form', `${formName}_${fieldName}_${action}`, {
      formName,
      fieldName,
      action,
      timestamp: Date.now()
    });
  }

  public trackAPICall(endpoint: string, method: string, responseTime: number, success: boolean, statusCode?: number): void {
    if (!this.isEnabled) return;

    this.trackEvent('api', 'call', {
      endpoint,
      method,
      responseTime,
      success,
      statusCode,
      timestamp: Date.now()
    });
  }

  private getCurrentABVariant(): string {
    // Интеграция с A/B тест менеджером
    return localStorage.getItem('current_ab_variant') || 'control';
  }

  private async flushEventQueue(force: boolean = false): Promise<void> {
    if (!this.isEnabled || this.eventQueue.length === 0) return;

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      const response = await fetch(`${this.apiUrl}/analytics/events/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${this.authToken}`
        },
        body: JSON.stringify({
          events,
          sessionId: this.sessionId,
          timestamp: Date.now()
        }),
        keepalive: force // Для отправки при закрытии страницы
      });

      if (!response.ok) {
        console.warn('Failed to send analytics events:', response.status);
        // Возвращаем события обратно в очередь при ошибке
        this.eventQueue.unshift(...events);
      }
    } catch (error) {
      console.warn('Analytics error:', error);
      // Возвращаем события обратно в очередь при ошибке
      this.eventQueue.unshift(...events);
    }
  }

  private async sendFeatureUsage(usage: FeatureUsage): Promise<void> {
    if (!this.isEnabled) return;

    try {
      await fetch(`${this.apiUrl}/analytics/feature-usage/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Token ${this.authToken}`
        },
        body: JSON.stringify(usage)
      });
    } catch (error) {
      console.warn('Feature usage tracking error:', error);
    }
  }

  // Методы для получения метрик

  public getSessionMetrics(): any {
    return {
      sessionId: this.sessionId,
      userId: this.userId,
      sessionStart: this.pageStartTime,
      performanceMetrics: this.performanceMetrics,
      eventsCount: this.eventQueue.length,
      activeInteractions: Array.from(this.interactions.keys())
    };
  }

  public exportSessionData(): string {
    const data = {
      session: this.getSessionMetrics(),
      events: this.eventQueue,
      userAgent: navigator.userAgent,
      timestamp: Date.now()
    };
    
    return JSON.stringify(data, null, 2);
  }
}

// Глобальный экземпляр аналитики
export const analytics = new AnalyticsManager();

// Хуки для React компонентов
export const useAnalytics = () => {
  return {
    trackEvent: analytics.trackEvent.bind(analytics),
    trackFeatureUsage: analytics.trackFeatureUsage.bind(analytics),
    startFeatureInteraction: analytics.startFeatureInteraction.bind(analytics),
    trackError: analytics.trackError.bind(analytics),
    trackPageView: analytics.trackPageView.bind(analytics),
    trackABTest: analytics.trackABTest.bind(analytics),
    trackConversion: analytics.trackConversion.bind(analytics),
    trackFormInteraction: analytics.trackFormInteraction.bind(analytics),
    trackAPICall: analytics.trackAPICall.bind(analytics)
  };
};

// Декоратор для автоматического трекинга функций
export function trackFunction(featureName: string, actionName?: string) {
  return function(target: any, propertyKey: string, descriptor: PropertyDescriptor) {
    const originalMethod = descriptor.value;
    const action = actionName || propertyKey;

    descriptor.value = async function(...args: any[]) {
      analytics.startFeatureInteraction(featureName, action);
      
      try {
        const result = await originalMethod.apply(this, args);
        analytics.trackFeatureUsage(featureName, action, true);
        return result;
      } catch (error) {
        analytics.trackFeatureUsage(featureName, action, false, { 
          error: error instanceof Error ? error.message : 'Unknown error' 
        });
        throw error;
      }
    };

    return descriptor;
  };
}

export default analytics;