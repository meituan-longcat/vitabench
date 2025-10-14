import threading
from typing import Dict, TypeVar, Generic, Type
from abc import ABC, abstractmethod

T = TypeVar('T')


class ThreadSafeBase(ABC, Generic[T]):
    """
    Thread-safe base class providing thread isolation capabilities
    
    This base class uses thread ID as the key to store instances for each thread,
    ensuring complete data isolation between different threads.
    
    Supports polymorphic design: parent classes can access instances of all subclasses.
    """
    
    def __init__(self):
        self._instances: Dict[int, Dict[str, T]] = {}
        self._lock = threading.Lock()
    
    @classmethod
    def _get_thread_instances(cls) -> Dict[str, T]:
        """
        Get all instances for the current thread
        
        Returns:
            Dict[str, T]: Dictionary of instances for the current thread
        """
        thread_id = threading.get_ident()
        
        if not hasattr(cls, '_global_instances'):
            cls._global_instances = {}
            cls._global_lock = threading.Lock()
        
        with cls._global_lock:
            if thread_id not in cls._global_instances:
                cls._global_instances[thread_id] = {}
            return cls._global_instances[thread_id]
    
    @classmethod
    def _get_polymorphic_instances(cls) -> Dict[str, T]:
        """
        Get all polymorphic instances for the current thread (including subclass instances)
        
        Returns:
            Dict[str, T]: All polymorphic instances for the current thread
        """
        thread_id = threading.get_ident()
        
        if not hasattr(cls, '_polymorphic_instances'):
            cls._polymorphic_instances = {}
            cls._polymorphic_lock = threading.Lock()
        
        with cls._polymorphic_lock:
            if thread_id not in cls._polymorphic_instances:
                cls._polymorphic_instances[thread_id] = {}
            return cls._polymorphic_instances[thread_id]
    
    @classmethod
    def clear_thread_data(cls):
        """
        Clear data for the current thread, used when starting a thread
        
        This method should be called at the beginning of each thread to ensure thread data isolation.
        """
        thread_id = threading.get_ident()
        
        if not hasattr(cls, '_global_instances'):
            cls._global_instances = {}
            cls._global_lock = threading.Lock()
        
        if not hasattr(cls, '_polymorphic_instances'):
            cls._polymorphic_instances = {}
            cls._polymorphic_lock = threading.Lock()
        
        with cls._global_lock:
            cls._global_instances[thread_id] = {}
        
        with cls._polymorphic_lock:
            cls._polymorphic_instances[thread_id] = {}
    
    @classmethod
    def clear_all(cls):
        """
        Clear all instances for the current thread
        """
        thread_id = threading.get_ident()
        
        if not hasattr(cls, '_global_instances'):
            cls._global_instances = {}
            cls._global_lock = threading.Lock()
        
        if not hasattr(cls, '_polymorphic_instances'):
            cls._polymorphic_instances = {}
            cls._polymorphic_lock = threading.Lock()
        
        with cls._global_lock:
            if thread_id in cls._global_instances:
                cls._global_instances[thread_id].clear()
        
        with cls._polymorphic_lock:
            if thread_id in cls._polymorphic_instances:
                cls._polymorphic_instances[thread_id].clear()
    
    @classmethod
    def get_all(cls) -> Dict[str, T]:
        """
        Get all instances for the current thread
        
        Returns:
            Dict[str, T]: All instances for the current thread
        """
        return cls._get_thread_instances()
    
    @classmethod
    def get_all_polymorphic(cls) -> Dict[str, T]:
        """
        Get all polymorphic instances for the current thread (including subclass instances)
        
        Returns:
            Dict[str, T]: All polymorphic instances for the current thread
        """
        return cls._get_polymorphic_instances()
    
    @classmethod
    def cleanup_thread(cls):
        """
        Clean up data from terminated threads
        
        This method can be called periodically to clean up data from threads that have ended.
        """
        if not hasattr(cls, '_global_instances'):
            return
        
        current_threads = {thread.ident for thread in threading.enumerate()}
        
        with cls._global_lock:
            dead_threads = [tid for tid in cls._global_instances.keys() if tid not in current_threads]
            for tid in dead_threads:
                del cls._global_instances[tid]
        
        if hasattr(cls, '_polymorphic_instances'):
            with cls._polymorphic_lock:
                dead_threads = [tid for tid in cls._polymorphic_instances.keys() if tid not in current_threads]
                for tid in dead_threads:
                    del cls._polymorphic_instances[tid]
    
    @abstractmethod
    def get_instance_key(self) -> str:
        """
        Get the unique key for the instance
        
        Returns:
            str: The unique key for the instance
        """
        pass
    
    def register_instance(self):
        """
        Register the current instance to thread storage
        """
        instances = self._get_thread_instances()
        instances[self.get_instance_key()] = self
    
    def register_polymorphic_instance(self, base_class: Type[T]):
        """
        Register the current instance to polymorphic storage
        
        Args:
            base_class: Base class type for polymorphic storage
        """
        if not hasattr(base_class, '_polymorphic_instances'):
            base_class._polymorphic_instances = {}
            base_class._polymorphic_lock = threading.Lock()
        
        thread_id = threading.get_ident()
        
        with base_class._polymorphic_lock:
            if thread_id not in base_class._polymorphic_instances:
                base_class._polymorphic_instances[thread_id] = {}
            base_class._polymorphic_instances[thread_id][self.get_instance_key()] = self


 