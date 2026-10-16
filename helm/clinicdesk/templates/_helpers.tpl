{{- define "clinicdesk.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "clinicdesk.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "clinicdesk.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/part-of: clinicdesk
app.kubernetes.io/instance: {{ .Release.Name }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end -}}

{{/* selector labels for one component: pass (dict "ctx" $ "component" "backend") */}}
{{- define "clinicdesk.selectorLabels" -}}
app.kubernetes.io/name: {{ include "clinicdesk.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "clinicdesk.backendName" -}}{{ include "clinicdesk.fullname" . }}-backend{{- end -}}
{{- define "clinicdesk.frontendName" -}}{{ include "clinicdesk.fullname" . }}-frontend{{- end -}}
{{- define "clinicdesk.postgresName" -}}{{ include "clinicdesk.fullname" . }}-postgres{{- end -}}

{{- define "clinicdesk.dbSecretName" -}}
{{- default (printf "%s-db" (include "clinicdesk.fullname" .)) .Values.postgres.existingSecret -}}
{{- end -}}

{{- define "clinicdesk.dbHost" -}}
{{- if .Values.postgres.enabled -}}
{{ include "clinicdesk.postgresName" . }}
{{- else -}}
{{ required "postgres.externalHost is required when postgres.enabled=false" .Values.postgres.externalHost }}
{{- end -}}
{{- end -}}

{{- define "clinicdesk.image" -}}
{{- printf "%s:%s" .image.repository (default .ctx.Chart.AppVersion (toString .image.tag)) -}}
{{- end -}}
