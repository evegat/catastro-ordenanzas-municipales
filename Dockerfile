# Dockerfile para Producción en Coolify (ordenanzas.evegat.cl)
FROM nginx:alpine

# Reemplazar configuración por defecto
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar activos del dashboard
COPY dashboard/ /usr/share/nginx/html/

# Exponer puerto HTTP estándar
EXPOSE 80

# Comando de inicio
CMD ["nginx", "-g", "daemon off;"]
