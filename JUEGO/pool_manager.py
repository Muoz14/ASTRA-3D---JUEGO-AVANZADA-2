from ursina import Entity, Vec3, color

class ObjectPool:
    def __init__(self):
        # Diccionario para agrupar entidades por su "tipo" o "clase"
        self.pools = {}

    def get_object(self, object_class, *args, pool_key=None, **kwargs):
        """
        Obtiene una entidad inactiva del pool. Usa pool_key si se requiere diferenciar (ej. por tier).
        """
        key = pool_key if pool_key else object_class
        pool = self.pools.setdefault(key, [])
        
        # Buscar el primer objeto inactivo
        for obj in pool:
            if not obj.enabled:
                obj.enable()
                # Si el objeto tiene un método 'reset', lo llamamos
                if hasattr(obj, 'reset'):
                    obj.reset(*args, **kwargs)
                return obj
                
        # Si no hay inactivos, crear uno nuevo y añadirlo al pool
        new_obj = object_class(*args, **kwargs)
        # Inyectamos referencias al pool en el objeto
        new_obj.pool = self
        new_obj.pool_key = key
        pool.append(new_obj)
        return new_obj

    def return_object(self, obj):
        """
        Devuelve el objeto al pool desactivándolo en lugar de destruirlo.
        """
        if obj.enabled:
            obj.disable()
            
            # Detener animaciones en curso (Panda3D secuencias) si existen
            if hasattr(obj, 'animations') and obj.animations:
                for anim in obj.animations:
                    anim.finish()
                obj.animations.clear()
