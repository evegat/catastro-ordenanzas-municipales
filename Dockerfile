# Dockerfile para Producción en Coolify (ordenanzas.evegat.cl)
FROM nginxinc/nginx-unprivileged:alpine

# Reemplazar configuración por defecto
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copiar activos del dashboard
COPY dashboard/ /usr/share/nginx/html/

# Exponer puerto HTTP estándar sin privilegios
EXPOSE 8080

# Healthcheck requerido por estándares de seguridad Trivy
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:8080/ || exit 1

# Usuario no-root explícito
USER 101

# Comando de inicio
CMD ["nginx", "-g", "daemon off;"]
