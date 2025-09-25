# Seguridad y Protección de Datos

## 1. Análisis del dataset
El dataset utilizado corresponde a registros estadísticos de accidentes de tránsito.  
Los campos principales incluyen: fecha, entidad, municipio, tipo de accidente, causas, condiciones del conductor (sexo, aliento alcohólico, uso de cinturón), clasificación del accidente y estado de la cifra.

### No contiene:
- Nombres de personas
- Documentos de identidad
- Direcciones exactas
- Datos sensibles directos

### Contiene datos potencialmente sensibles:
- **Ubicación (entidad y municipio):** aunque son datos agregados, permiten identificar zonas geográficas con alta siniestralidad.
- **Sexo y edad del conductor:** pueden considerarse datos personales indirectos si se cruzan con otras fuentes.
- **Condiciones del accidente (alcohol, cinturón):** información que puede dar lugar a estigmatización o uso indebido.

---

## 2. Riesgos detectados
- **Reidentificación:** si se combinan estos datos con otras bases externas (p. ej. registros policiales), podría identificarse a individuos.
- **Estigmatización:** perfiles de conductores (ej. hombres jóvenes con alcohol) pueden usarse para sesgos injustos.
- **Exposición no controlada:** si la API es pública y sin protección, cualquiera podría extraer y redistribuir los datos. (En mi caso si es publica)

---

## 3. Medidas mínimas de mitigación
1. **Anonimización y reducción de granularidad:**
   - No publicar identificadores que puedan cruzarse con datos externos.
   - Mantener la edad en rangos (ej. 18–25, 26–40, 41–60, >60) en lugar de valores exactos. (Esto no se hace por perdida de informacion exacta)

2. **Protección de acceso:**
   - Endpoints sensibles (actualización de datos) deben estar protegidos con autenticación mediante **JWT** o similar. (Para el proyecto actual se hizo el cifrado con JWT)

3. **Limitación de uso:**
   - Documentar que los datos son únicamente para fines **estadísticos y educativos**.
   - Prevenir descargas masivas no autorizadas con rate limiting en la API.

4. **Cifrado y transporte seguro:**
   - Usar **HTTPS** para todas las comunicaciones.
   - En producción, nunca exponer credenciales en texto plano (usar variables de entorno).(Actualmente se usan variables de entorno)

## 4. Conclusión
El dataset no contiene identificadores directos, pero sí información que, en combinación con otras fuentes, podría usarse para inferencias sensibles.  
Con anonimización parcial, control de acceso y políticas de uso claro, los riesgos se reducen de forma significativa.
