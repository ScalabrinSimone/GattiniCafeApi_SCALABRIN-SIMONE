""" File per customizzare i permessi di accesso agli endpoint. """

from rest_framework import permissions

# Permesso solo a proprietario o admin (es. per modificare un ordine, solo chi l'ha fatto o admin può farlo).
class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:  # Admin può fare tutto.
            return True
        return obj.utente_id == request.user.id  # Solo proprietario dell'ordine può modificare.
    
class IsAdminUser(permissions.IsAdminUser):
    pass # staff = True.