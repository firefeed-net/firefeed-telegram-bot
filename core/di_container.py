# di_container.py - Dependency Injection Container
import logging
from typing import Dict, Any, Type, TypeVar, Optional
from core.interfaces import (
    ITelegramUserService, IUserRepository,
    ITelegramRepository, IDatabasePool
)

logger = logging.getLogger(__name__)

T = TypeVar('T')


class DIContainer:
    """Simple Dependency Injection Container"""

    def __init__(self):
        self._services: Dict[Type, Any] = {}
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, callable] = {}

    def register(self, interface: Type[T], implementation: Type[T], singleton: bool = True) -> None:
        """Register a service implementation"""
        if singleton:
            self._services[interface] = implementation
        else:
            self._factories[interface] = implementation

    def register_instance(self, interface: Type[T], instance: T) -> None:
        """Register a singleton instance"""
        self._singletons[interface] = instance

    def register_factory(self, interface: Type[T], factory: callable) -> None:
        """Register a factory function"""
        self._factories[interface] = factory

    def resolve(self, interface: Type[T]) -> T:
        """Resolve a service instance"""
        # Check singletons first
        if interface in self._singletons:
            return self._singletons[interface]

        # Check services
        if interface in self._services:
            impl_class = self._services[interface]
            instance = self._instantiate(impl_class)
            self._singletons[interface] = instance  # Cache as singleton
            return instance

        # Check factories
        if interface in self._factories:
            factory = self._factories[interface]
            return factory()

        raise ValueError(f"No registration found for {interface}")

    def _instantiate(self, cls: Type[T]) -> T:
        """Instantiate a class with dependency injection"""
        import inspect

        # Get constructor parameters
        init_signature = inspect.signature(cls.__init__)
        params = {}

        for param_name, param in init_signature.parameters.items():
            if param_name == 'self':
                continue

            # Skip *args and **kwargs parameters
            if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
                continue

            # Try to resolve parameter type
            if param.annotation != inspect.Parameter.empty:
                try:
                    params[param_name] = self.resolve(param.annotation)
                except ValueError:
                    # If can't resolve, try to get default value
                    if param.default != inspect.Parameter.empty:
                        params[param_name] = param.default
                    else:
                        raise ValueError(f"Cannot resolve parameter {param_name} for {cls}")
            elif param.default != inspect.Parameter.empty:
                params[param_name] = param.default
            else:
                raise ValueError(f"Cannot resolve parameter {param_name} for {cls}")

        # If no parameters needed, just instantiate
        if not params:
            return cls()

        return cls(**params)

    def clear(self) -> None:
        """Clear all registrations and instances"""
        self._services.clear()
        self._singletons.clear()
        self._factories.clear()


# Global DI container instance
di_container = DIContainer()


async def setup_di_container() -> DIContainer:
    """Setup the global DI container with services needed for Telegram bot"""
    global di_container

    # Import configuration
    from core.config.services_config import get_service_config

    config = get_service_config()

    # Register config as both dict and ServiceConfig first
    di_container.register_instance(dict, config)
    di_container.register_instance(type(config), config)

    # Import services
    from core.services.database_pool_adapter import DatabasePoolAdapter
    from core.services.telegram_user_service import TelegramUserService

    # Register database pool adapter
    # For testing/development, create a mock pool if database is not available
    try:
        # Create database pool using config
        import aiopg

        db_config = {
            "host": config.database.host,
            "user": config.database.user,
            "password": config.database.password,
            "database": config.database.name,
            "port": config.database.port,
            "minsize": config.database.minsize,
            "maxsize": config.database.maxsize,
        }

        # Log database connection config for debugging
        masked_config = db_config.copy()
        masked_config["password"] = "***" if db_config["password"] else None
        logger.info(f"Database connection config: {masked_config}")

        db_pool = await aiopg.create_pool(**db_config)

        db_pool_adapter = DatabasePoolAdapter(db_pool)
        di_container.register_instance(IDatabasePool, db_pool_adapter)
    except Exception as e:
        logger.warning(f"Database not available, creating mock pool: {e}")
        # Create mock pool for testing/development
        class MockPool:
            def acquire(self):
                class MockConn:
                    def __await__(self):
                        async def _await():
                            return self
                        return _await().__await__()
                    def cursor(self):
                        class MockCursor:
                            rowcount = 0
                            description = []
                            async def execute(self, *args, **kwargs): pass
                            async def fetchone(self): return None
                            async def fetchall(self): return []
                            def __aiter__(self): return self
                            async def __anext__(self): raise StopAsyncIteration
                            async def __aenter__(self): return self
                            async def __aexit__(self, *args): pass
                        return MockCursor()
                    async def __aenter__(self): return self
                    async def __aexit__(self, *args): pass
                return MockConn()
            def release(self, conn): pass
            async def close(self): pass
            async def wait_closed(self): pass

        db_pool = MockPool()
        db_pool_adapter = DatabasePoolAdapter(db_pool)
        di_container.register_instance(IDatabasePool, db_pool_adapter)

    # Register Redis client
    import redis
    redis_client = redis.Redis(
        host=config.redis.host,
        port=config.redis.port,
        username=config.redis.username,
        password=config.redis.password,
        db=config.redis.db,
        decode_responses=True
    )
    di_container.register_instance(redis.Redis, redis_client)

    # Register repositories
    from core.repositories import UserRepository, TelegramRepository
    from interfaces import IUserRepository, ITelegramRepository

    di_container.register_factory(IUserRepository, lambda: UserRepository(db_pool_adapter))
    di_container.register_factory(ITelegramRepository, lambda: TelegramRepository(db_pool_adapter))

    # Register user services
    di_container.register_factory(ITelegramUserService, lambda: TelegramUserService(di_container.resolve(IUserRepository)))

    logger.info("DI container setup completed for Telegram bot")
    return di_container


def get_service(interface: Type[T]) -> T:
    """Get a service instance from the global DI container"""
    return di_container.resolve(interface)


def resolve(interface: Type[T]) -> T:
    """Resolve a service instance from the global DI container"""
    return di_container.resolve(interface)


async def get_db_pool():
    """Get database pool instance from DI container"""
    db_pool_adapter = get_service(IDatabasePool)
    # Return the actual pool from the adapter
    async with db_pool_adapter.acquire() as conn:
        # This is a bit hacky, but we need to return the pool, not a connection
        # The adapter's _pool attribute contains the actual aiopg pool
        return db_pool_adapter._pool