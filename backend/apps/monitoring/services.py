"""
Monitoring services for algorithm tracking and alerting.
"""
import time
import logging
import hashlib
import traceback
from typing import Dict, List, Optional, Any
from decimal import Decimal
from django.utils import timezone
from django.db import connection
from django.core.cache import cache
from django.conf import settings
import psutil
import redis

from .models import AlgorithmExecution, AlgorithmAlert, SystemHealth, AlgorithmBaseline
from apps.products.models import Product


logger = logging.getLogger('apps.monitoring')


class AlgorithmMonitor:
    """Monitor algorithm execution and detect regressions."""
    
    def __init__(self):
        self.current_execution = None
        self.start_time = None
        self.start_queries = len(connection.queries) if settings.DEBUG else 0
    
    def start_monitoring(self, execution_type: str, products_count: int = 0) -> AlgorithmExecution:
        """Start monitoring an algorithm execution."""
        self.start_time = time.time()
        self.start_queries = len(connection.queries) if settings.DEBUG else 0
        
        self.current_execution = AlgorithmExecution.objects.create(
            execution_type=execution_type,
            products_processed=products_count,
            algorithm_version=self._get_algorithm_version(),
        )
        
        logger.info(f"Started monitoring {execution_type} for {products_count} products")
        return self.current_execution
    
    def finish_monitoring(self, products_needing_production: int = 0, 
                         total_production_units: Decimal = Decimal('0'),
                         errors_count: int = 0, error_details: str = "") -> AlgorithmExecution:
        """Finish monitoring and save results."""
        if not self.current_execution:
            logger.warning("finish_monitoring called without start_monitoring")
            return None
        
        self.current_execution.products_needing_production = products_needing_production
        self.current_execution.total_production_units = total_production_units
        self.current_execution.errors_encountered = errors_count
        self.current_execution.error_details = error_details
        
        # Calculate performance metrics
        if self.start_time:
            duration = time.time() - self.start_time
            self.current_execution.duration_seconds = Decimal(str(duration))
            
            if self.current_execution.products_processed > 0:
                avg_time_ms = (duration * 1000) / self.current_execution.products_processed
                self.current_execution.average_calculation_time_ms = Decimal(str(avg_time_ms))
        
        # Database queries (if DEBUG is enabled)
        if settings.DEBUG:
            current_queries = len(connection.queries)
            self.current_execution.database_queries = current_queries - self.start_queries
        
        # Memory usage
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self.current_execution.memory_usage_mb = Decimal(str(memory_mb))
        except:
            pass
        
        self.current_execution.mark_finished()
        
        # Check for performance alerts
        self._check_performance_alerts(self.current_execution)
        
        logger.info(f"Finished monitoring {self.current_execution.execution_type}: "
                   f"{duration:.2f}s, {products_needing_production} products need production")
        
        execution = self.current_execution
        self.current_execution = None
        return execution
    
    def _get_algorithm_version(self) -> str:
        """Get algorithm version (hash of key algorithm files)."""
        try:
            # In a real environment, this could be git commit hash
            # For now, create hash of key model methods
            from apps.products.models import Product
            
            methods_source = ""
            for method_name in ['calculate_production_need', 'calculate_priority', 'classify_product_type']:
                method = getattr(Product, method_name, None)
                if method:
                    methods_source += str(method.__code__.co_code)
            
            return hashlib.sha256(methods_source.encode()).hexdigest()[:16]
        except:
            return "unknown"
    
    def _check_performance_alerts(self, execution: AlgorithmExecution):
        """Check for performance degradation alerts."""
        if not execution.duration_seconds:
            return
        
        # Define performance thresholds
        thresholds = {
            'single_product': {'critical': 1.0, 'warning': 0.5},  # seconds
            'batch_recalculation': {'critical': 30.0, 'warning': 15.0},
            'production_list': {'critical': 10.0, 'warning': 5.0},
            'monitoring_check': {'critical': 5.0, 'warning': 2.0},
        }
        
        threshold = thresholds.get(execution.execution_type, {'critical': 10.0, 'warning': 5.0})
        duration = float(execution.duration_seconds)
        
        if duration > threshold['critical']:
            self._create_alert(
                alert_type='performance',
                severity='critical',
                title=f"Critical Performance Degradation in {execution.execution_type}",
                description=f"Algorithm execution took {duration:.2f}s, exceeding critical threshold of {threshold['critical']}s",
                details={'execution_id': execution.id, 'duration': duration, 'threshold': threshold['critical']},
                execution=execution
            )
        elif duration > threshold['warning']:
            self._create_alert(
                alert_type='performance',
                severity='medium',
                title=f"Performance Warning in {execution.execution_type}",
                description=f"Algorithm execution took {duration:.2f}s, exceeding warning threshold of {threshold['warning']}s",
                details={'execution_id': execution.id, 'duration': duration, 'threshold': threshold['warning']},
                execution=execution
            )
    
    def run_regression_tests(self) -> Dict[str, Any]:
        """Run algorithm regression tests against baseline."""
        logger.info("Running algorithm regression tests")
        
        monitor = AlgorithmMonitor()
        execution = monitor.start_monitoring('monitoring_check')
        
        try:
            baselines = AlgorithmBaseline.objects.filter(is_active=True)
            results = []
            all_passed = True
            
            for baseline in baselines:
                # Create test product
                product = Product(
                    article=baseline.article,
                    current_stock=baseline.current_stock,
                    sales_last_2_months=baseline.sales_last_2_months
                )
                
                # Test calculations
                actual_production = product.calculate_production_need()
                actual_type = product.classify_product_type()
                actual_priority = product.calculate_priority()
                
                # Compare results
                production_match = actual_production == baseline.expected_production_need
                type_match = actual_type == baseline.expected_product_type
                priority_match = actual_priority == baseline.expected_priority
                
                test_passed = production_match and type_match and priority_match
                if not test_passed:
                    all_passed = False
                
                results.append({
                    'test_case': baseline.test_case_name,
                    'article': baseline.article,
                    'production_need': {
                        'expected': str(baseline.expected_production_need),
                        'actual': str(actual_production),
                        'match': production_match
                    },
                    'product_type': {
                        'expected': baseline.expected_product_type,
                        'actual': actual_type,
                        'match': type_match
                    },
                    'priority': {
                        'expected': baseline.expected_priority,
                        'actual': actual_priority,
                        'match': priority_match
                    },
                    'passed': test_passed
                })
            
            # Create alert if regression detected
            if not all_passed:
                failed_tests = [r for r in results if not r['passed']]
                self._create_alert(
                    alert_type='regression',
                    severity='critical',
                    title="Algorithm Regression Detected",
                    description=f"Algorithm regression detected in {len(failed_tests)} test case(s)",
                    details={
                        'failed_tests': failed_tests,
                        'total_tests': len(results),
                        'failed_count': len(failed_tests)
                    },
                    execution=execution
                )
            
            monitor.finish_monitoring(
                products_needing_production=len([r for r in results if r['passed']]),
                total_production_units=Decimal('0'),
                errors_count=0 if all_passed else len([r for r in results if not r['passed']])
            )
            
            return {
                'all_passed': all_passed,
                'total_tests': len(results),
                'passed_tests': len([r for r in results if r['passed']]),
                'failed_tests': len([r for r in results if not r['passed']]),
                'results': results
            }
            
        except Exception as e:
            logger.error(f"Error running regression tests: {e}")
            monitor.finish_monitoring(errors_count=1, error_details=str(e))
            raise
    
    def _create_alert(self, alert_type: str, severity: str, title: str, 
                     description: str, details: Dict = None, execution: AlgorithmExecution = None):
        """Create an algorithm alert."""
        alert = AlgorithmAlert.objects.create(
            alert_type=alert_type,
            severity=severity,
            title=title,
            description=description,
            details=details or {},
            execution=execution
        )
        
        logger.warning(f"Created {severity} alert: {title}")
        
        # Send notifications
        self._send_alert_notifications(alert)
        
        return alert
    
    def _send_alert_notifications(self, alert: AlgorithmAlert):
        """Send alert notifications to configured channels."""
        notifications_sent = []
        
        try:
            # Send to Slack if configured
            slack_webhook = getattr(settings, 'SLACK_WEBHOOK_URL', None)
            if slack_webhook:
                self._send_slack_notification(alert, slack_webhook)
                notifications_sent.append('slack')
            
            # Send email if configured
            if getattr(settings, 'EMAIL_ALERTS_ENABLED', False):
                self._send_email_notification(alert)
                notifications_sent.append('email')
            
            # Update alert with notification status
            alert.notifications_sent = notifications_sent
            alert.save()
            
        except Exception as e:
            logger.error(f"Error sending alert notifications: {e}")
    
    def _send_slack_notification(self, alert: AlgorithmAlert, webhook_url: str):
        """Send alert to Slack."""
        import requests
        
        color_map = {
            'critical': '#FF0000',
            'high': '#FF8800',
            'medium': '#FFAA00',
            'low': '#00AA00'
        }
        
        message = {
            "attachments": [{
                "color": color_map.get(alert.severity, '#808080'),
                "title": f"PrintFarm Alert: {alert.title}",
                "text": alert.description,
                "fields": [
                    {"title": "Severity", "value": alert.severity.upper(), "short": True},
                    {"title": "Type", "value": alert.alert_type.replace('_', ' ').title(), "short": True},
                    {"title": "Time", "value": alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC'), "short": False},
                ],
                "footer": "PrintFarm Monitoring"
            }]
        }
        
        response = requests.post(webhook_url, json=message, timeout=10)
        response.raise_for_status()
    
    def _send_email_notification(self, alert: AlgorithmAlert):
        """Send alert via email."""
        from django.core.mail import send_mail
        
        subject = f"[PrintFarm {alert.severity.upper()}] {alert.title}"
        message = f"""
PrintFarm Alert Notification

Alert Type: {alert.alert_type.replace('_', ' ').title()}
Severity: {alert.severity.upper()}
Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S UTC')}

Description:
{alert.description}

Details:
{alert.details}

Please investigate immediately if this is a critical alert.

---
PrintFarm Monitoring System
        """
        
        recipient_list = getattr(settings, 'ALERT_EMAIL_RECIPIENTS', [])
        if recipient_list:
            send_mail(
                subject=subject,
                message=message,
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@printfarm.com'),
                recipient_list=recipient_list,
                fail_silently=False
            )


class SystemHealthMonitor:
    """Monitor overall system health."""
    
    def collect_health_metrics(self) -> SystemHealth:
        """Collect and save current system health metrics."""
        health = SystemHealth()
        
        try:
            # API health (mock - in real app, make actual API calls)
            health.api_response_time_ms = self._measure_api_response_time()
            health.api_error_rate = self._get_api_error_rate()
            
            # Database health
            health.database_connection_time_ms = self._measure_database_connection_time()
            health.database_query_time_avg_ms = self._get_average_query_time()
            health.database_connections_active = self._get_active_connections()
            
            # Redis health
            health.redis_response_time_ms = self._measure_redis_response_time()
            health.redis_memory_usage_mb = self._get_redis_memory_usage()
            
            # Application metrics
            health.total_products = Product.objects.count()
            health.products_needing_production = Product.objects.filter(production_needed__gt=0).count()
            
            # System resources
            health.memory_usage_percent = self._get_memory_usage_percent()
            health.cpu_usage_percent = self._get_cpu_usage_percent()
            health.disk_usage_percent = self._get_disk_usage_percent()
            
            # Calculate overall health score
            health.health_score = self._calculate_health_score(health)
            health.is_healthy = health.health_score >= 80  # 80% threshold
            
            health.save()
            
            # Check for health alerts
            self._check_health_alerts(health)
            
            return health
            
        except Exception as e:
            logger.error(f"Error collecting health metrics: {e}")
            health.is_healthy = False
            health.health_score = Decimal('0')
            health.save()
            return health
    
    def _measure_api_response_time(self) -> Decimal:
        """Measure API response time."""
        start_time = time.time()
        try:
            # In real implementation, make actual API call
            time.sleep(0.05)  # Simulate API call
            duration_ms = (time.time() - start_time) * 1000
            return Decimal(str(round(duration_ms, 2)))
        except:
            return Decimal('999999')  # High value indicates failure
    
    def _get_api_error_rate(self) -> Decimal:
        """Get API error rate percentage."""
        # In real implementation, calculate from logs or metrics
        return Decimal('0.5')  # 0.5% error rate
    
    def _measure_database_connection_time(self) -> Decimal:
        """Measure database connection time."""
        start_time = time.time()
        try:
            from django.db import connection
            connection.ensure_connection()
            duration_ms = (time.time() - start_time) * 1000
            return Decimal(str(round(duration_ms, 2)))
        except:
            return Decimal('999999')
    
    def _get_average_query_time(self) -> Decimal:
        """Get average database query time."""
        # In real implementation, analyze query logs
        return Decimal('25.5')  # Mock value
    
    def _get_active_connections(self) -> int:
        """Get number of active database connections."""
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT count(*) FROM pg_stat_activity WHERE state = 'active'")
                return cursor.fetchone()[0]
        except:
            return 0
    
    def _measure_redis_response_time(self) -> Decimal:
        """Measure Redis response time."""
        try:
            r = redis.Redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'))
            start_time = time.time()
            r.ping()
            duration_ms = (time.time() - start_time) * 1000
            return Decimal(str(round(duration_ms, 2)))
        except:
            return Decimal('999999')
    
    def _get_redis_memory_usage(self) -> Decimal:
        """Get Redis memory usage in MB."""
        try:
            r = redis.Redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'))
            info = r.info('memory')
            memory_mb = info['used_memory'] / 1024 / 1024
            return Decimal(str(round(memory_mb, 2)))
        except:
            return Decimal('0')
    
    def _get_memory_usage_percent(self) -> Decimal:
        """Get system memory usage percentage."""
        try:
            memory = psutil.virtual_memory()
            return Decimal(str(round(memory.percent, 2)))
        except:
            return Decimal('0')
    
    def _get_cpu_usage_percent(self) -> Decimal:
        """Get system CPU usage percentage."""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            return Decimal(str(round(cpu_percent, 2)))
        except:
            return Decimal('0')
    
    def _get_disk_usage_percent(self) -> Decimal:
        """Get disk usage percentage."""
        try:
            disk = psutil.disk_usage('/')
            return Decimal(str(round(disk.percent, 2)))
        except:
            return Decimal('0')
    
    def _calculate_health_score(self, health: SystemHealth) -> Decimal:
        """Calculate overall health score (0-100)."""
        score = Decimal('100')
        
        # Deduct points for poor performance
        if health.api_response_time_ms and health.api_response_time_ms > 1000:  # > 1 second
            score -= Decimal('20')
        elif health.api_response_time_ms and health.api_response_time_ms > 500:  # > 0.5 seconds
            score -= Decimal('10')
        
        if health.database_connection_time_ms and health.database_connection_time_ms > 100:  # > 100ms
            score -= Decimal('15')
        
        if health.redis_response_time_ms and health.redis_response_time_ms > 50:  # > 50ms
            score -= Decimal('10')
        
        # System resource usage
        if health.memory_usage_percent and health.memory_usage_percent > 90:
            score -= Decimal('20')
        elif health.memory_usage_percent and health.memory_usage_percent > 80:
            score -= Decimal('10')
        
        if health.cpu_usage_percent and health.cpu_usage_percent > 90:
            score -= Decimal('15')
        elif health.cpu_usage_percent and health.cpu_usage_percent > 80:
            score -= Decimal('5')
        
        if health.disk_usage_percent and health.disk_usage_percent > 95:
            score -= Decimal('25')
        elif health.disk_usage_percent and health.disk_usage_percent > 85:
            score -= Decimal('10')
        
        return max(score, Decimal('0'))
    
    def _check_health_alerts(self, health: SystemHealth):
        """Check for health-related alerts."""
        monitor = AlgorithmMonitor()
        
        if not health.is_healthy:
            monitor._create_alert(
                alert_type='anomaly',
                severity='high',
                title="System Health Degradation",
                description=f"System health score dropped to {health.health_score}%",
                details={'health_score': float(health.health_score)}
            )
        
        # Check specific thresholds
        if health.api_response_time_ms and health.api_response_time_ms > 2000:  # > 2 seconds
            monitor._create_alert(
                alert_type='performance',
                severity='critical',
                title="API Response Time Critical",
                description=f"API response time is {health.api_response_time_ms}ms",
                details={'response_time_ms': float(health.api_response_time_ms)}
            )
        
        if health.memory_usage_percent and health.memory_usage_percent > 95:
            monitor._create_alert(
                alert_type='error',
                severity='critical',
                title="Critical Memory Usage",
                description=f"Memory usage is {health.memory_usage_percent}%",
                details={'memory_percent': float(health.memory_usage_percent)}
            )