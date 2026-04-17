"""VocaLive - Comprehensive Resource Cleanup System
Sistem cleanup menyeluruh untuk semua komponen aplikasi
"""

import gc
import logging
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger('VocaLive')

class ComprehensiveCleanup:
    """Comprehensive cleanup system untuk semua resource aplikasi"""

    def __init__(self):
        self.cleanup_errors = []
        self.cleanup_stats = {
            "components_cleaned": 0,
            "errors_encountered": 0,
            "cleanup_time_ms": 0
        }

    def cleanup_all(self, force_cleanup: bool = False) -> Dict[str, Any]:
        """Main cleanup function untuk semua komponen aplikasi"""
        start_time = time.time()
        logger.info("🧹 Starting comprehensive application cleanup...")

        try:
            # 1. Cleanup PyTchat Listeners
            self._cleanup_pytchat_listeners()

            # 2. Cleanup TTS Engine
            self._cleanup_tts_engine()

            # 3. Cleanup API Clients
            self._cleanup_api_clients()

            # 4. Cleanup Cache Systems
            self._cleanup_cache_systems()

            # 5. Cleanup Local Storage
            self._cleanup_local_storage()

            # 6. Cleanup OAuth Sessions
            self._cleanup_oauth_sessions()

            # 7. Cleanup Lightweight AI
            self._cleanup_lightweight_ai()

            # 8. Cleanup Auto Cache Manager
            self._cleanup_auto_cache_manager()

            # 9. Cleanup Viewer Memory
            self._cleanup_viewer_memory()

            # 10. Cleanup Network Sessions
            self._cleanup_network_sessions()

            # 11. Force Garbage Collection
            self._force_garbage_collection()

            # Calculate cleanup time
            cleanup_time = (time.time() - start_time) * 1000
            self.cleanup_stats["cleanup_time_ms"] = cleanup_time
            self.cleanup_stats["errors_encountered"] = len(self.cleanup_errors)

            if self.cleanup_errors:
                logger.warning(f"Cleanup completed with {len(self.cleanup_errors)} errors")
                for error in self.cleanup_errors:
                    logger.warning(f"  - {error}")
            else:
                logger.info(f"✅ Comprehensive cleanup completed successfully in {cleanup_time:.1f}ms")

            return {
                "success": True,
                "stats": self.cleanup_stats,
                "errors": self.cleanup_errors
            }

        except Exception as e:
            logger.error(f"❌ Critical error during comprehensive cleanup: {e}")
            self.cleanup_errors.append(f"Critical cleanup error: {e}")
            return {
                "success": False,
                "stats": self.cleanup_stats,
                "errors": self.cleanup_errors
            }

    def _cleanup_pytchat_listeners(self):
        """Cleanup PyTchat listeners dan related components"""
        try:
            logger.debug("🔄 Cleaning up PyTchat listeners...")

            # Stop global pytchat listener
            try:
                from modules_client.pytchat_listener import stop_pytchat_listener
                stop_pytchat_listener()
                logger.debug("✅ Global PyTchat listener stopped")
            except ImportError:
                logger.debug("⚠️ PyTchat listener module not available")
            except Exception as e:
                self.cleanup_errors.append(f"PyTchat listener stop error: {e}")

            # Cleanup PyTchat EXE Fix instances
            try:
                from modules_client.pytchat_exe_fixed import PyTchatEXEFix
                # Reset initialization state if needed
                if hasattr(PyTchatEXEFix, '_initialized'):
                    PyTchatEXEFix._initialized = False
                    PyTchatEXEFix._pytchat = None
                logger.debug("✅ PyTchat EXE Fix cleaned")
            except ImportError:
                logger.debug("⚠️ PyTchat EXE Fix module not available")
            except Exception as e:
                self.cleanup_errors.append(f"PyTchat EXE Fix cleanup error: {e}")

            self.cleanup_stats["components_cleaned"] += 1

        except Exception as e:
            self.cleanup_errors.append(f"PyTchat cleanup error: {e}")

    def _cleanup_tts_engine(self):
        """Cleanup TTS engine resources"""
        try:
            logger.debug("🔊 Cleaning up TTS engine...")

            from modules_server.tts_engine import cleanup_tts_engine
            cleanup_tts_engine()
            logger.debug("✅ TTS engine cleaned")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ TTS engine module not available")
        except Exception as e:
            self.cleanup_errors.append(f"TTS engine cleanup error: {e}")

    def _cleanup_api_clients(self):
        """Cleanup API clients dan sessions"""
        try:
            logger.debug("🌐 Cleaning up API clients...")

            from modules_client.api import cleanup_api_client
            cleanup_api_client()
            logger.debug("✅ API clients cleaned")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ API client module not available")
        except Exception as e:
            self.cleanup_errors.append(f"API client cleanup error: {e}")

    def _cleanup_cache_systems(self):
        """Cleanup cache management systems"""
        try:
            logger.debug("💾 Cleaning up cache systems...")

            # Cleanup CacheManager (module removed — skip silently)
            try:
                from modules_client.cache_manager import CacheManager
                cache_manager = CacheManager()
                cache_manager.cleanup()
                logger.debug("✅ Cache manager cleaned")
            except ImportError:
                pass  # module tidak ada, skip
            except Exception as e:
                self.cleanup_errors.append(f"Cache manager cleanup error: {e}")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ Cache manager module not available")
        except Exception as e:
            self.cleanup_errors.append(f"Cache systems cleanup error: {e}")

    def _cleanup_local_storage(self):
        """Cleanup local viewer storage"""
        try:
            logger.debug("🗄️ Cleaning up local storage...")

            from modules_client.local_viewer_storage import shutdown_local_storage
            shutdown_local_storage()
            logger.debug("✅ Local storage cleaned")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ Local storage module not available")
        except Exception as e:
            self.cleanup_errors.append(f"Local storage cleanup error: {e}")

    def _cleanup_oauth_sessions(self):
        """Cleanup OAuth sessions"""
        try:
            logger.debug("🔐 Cleaning up OAuth sessions...")

            from modules_client.google_oauth import cleanup_oauth_session
            cleanup_oauth_session()
            logger.debug("✅ OAuth sessions cleaned")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ OAuth module not available")
        except Exception as e:
            self.cleanup_errors.append(f"OAuth cleanup error: {e}")

    def _cleanup_lightweight_ai(self):
        """Cleanup Lightweight AI system"""
        try:
            logger.debug("🤖 Cleaning up Lightweight AI...")

            from modules_client.lightweight_ai import LightweightAI
            # Get global instance if exists
            try:
                ai_instance = LightweightAI()
                ai_instance.shutdown()
                logger.debug("✅ Lightweight AI cleaned")
            except Exception as e:
                self.cleanup_errors.append(f"Lightweight AI cleanup error: {e}")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ Lightweight AI module not available")
        except Exception as e:
            self.cleanup_errors.append(f"Lightweight AI cleanup error: {e}")

    def _cleanup_auto_cache_manager(self):
        """Cleanup Auto Cache Manager"""
        try:
            logger.debug("🗑️ Cleaning up Auto Cache Manager...")

            from modules_client.auto_cache_manager import get_cache_manager
            cache_manager = get_cache_manager()
            # Auto cache manager doesn't have explicit cleanup method
            # but we can trigger emergency cleanup if needed
            logger.debug("✅ Auto Cache Manager checked")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ Auto Cache Manager module not available")
        except Exception as e:
            self.cleanup_errors.append(f"Auto Cache Manager cleanup error: {e}")

    def _cleanup_viewer_memory(self):
        """Cleanup Viewer Memory system"""
        try:
            logger.debug("👥 Cleaning up Viewer Memory...")

            from modules_client.viewer_memory import ViewerMemory
            viewer_memory = ViewerMemory()
            # Trigger cleanup of old data
            viewer_memory._cleanup_old_data()
            logger.debug("✅ Viewer Memory cleaned")

            self.cleanup_stats["components_cleaned"] += 1

        except ImportError:
            logger.debug("⚠️ Viewer Memory module not available")
        except Exception as e:
            self.cleanup_errors.append(f"Viewer Memory cleanup error: {e}")

    def _cleanup_network_sessions(self):
        """Cleanup global network sessions"""
        try:
            logger.debug("🌐 Cleaning up network sessions...")

            # Cleanup requests sessions in various modules
            import requests

            # Close any remaining sessions
            try:
                # Force close connection pools
                requests.adapters.DEFAULT_POOLBLOCK = True
                requests.adapters.DEFAULT_POOLSIZE = 0
                logger.debug("✅ Network sessions cleaned")
            except Exception as e:
                self.cleanup_errors.append(f"Network session cleanup error: {e}")

            self.cleanup_stats["components_cleaned"] += 1

        except Exception as e:
            self.cleanup_errors.append(f"Network cleanup error: {e}")

    def _force_garbage_collection(self):
        """Force comprehensive garbage collection"""
        try:
            logger.debug("🗑️ Running garbage collection...")

            # Multiple garbage collection passes
            collected_objects = 0
            for i in range(3):
                collected = gc.collect()
                collected_objects += collected
                if collected == 0:
                    break

            logger.debug(f"✅ Garbage collection completed, collected {collected_objects} objects")

            self.cleanup_stats["components_cleaned"] += 1

        except Exception as e:
            self.cleanup_errors.append(f"Garbage collection error: {e}")

    def emergency_cleanup(self) -> Dict[str, Any]:
        """Emergency cleanup untuk situasi kritis"""
        logger.warning("🚨 Running emergency cleanup...")

        try:
            # Force stop semua threads
            main_thread = threading.main_thread()
            for thread in threading.enumerate():
                if thread != main_thread and thread.is_alive():
                    try:
                        if hasattr(thread, 'stop'):
                            thread.stop()
                        thread.join(timeout=1.0)
                        if thread.is_alive():
                            logger.warning(f"⚠️ Thread {thread.name} did not stop gracefully")
                    except Exception as e:
                        logger.warning(f"Error stopping thread {thread.name}: {e}")

            # Force cleanup semua resource
            result = self.cleanup_all(force_cleanup=True)

            # Force exit jika diperlukan
            if not result["success"]:
                logger.error("❌ Emergency cleanup failed, forcing exit")
                sys.exit(1)

            return result

        except Exception as e:
            logger.error(f"❌ Critical error in emergency cleanup: {e}")
            return {
                "success": False,
                "error": str(e)
            }

# Global cleanup instance
_global_cleanup = ComprehensiveCleanup()

def cleanup_all_resources(force_cleanup: bool = False) -> Dict[str, Any]:
    """Global function untuk cleanup semua resource aplikasi"""
    return _global_cleanup.cleanup_all(force_cleanup=force_cleanup)

def emergency_cleanup() -> Dict[str, Any]:
    """Global function untuk emergency cleanup"""
    return _global_cleanup.emergency_cleanup()

def get_cleanup_stats() -> Dict[str, Any]:
    """Get cleanup statistics"""
    return _global_cleanup.cleanup_stats.copy()

if __name__ == "__main__":
    # Test cleanup system
    logger.info("Testing comprehensive cleanup system...")
    result = cleanup_all_resources()
    print(f"Cleanup result: {result}")
