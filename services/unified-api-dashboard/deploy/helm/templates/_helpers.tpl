{{/*
Expand the name of the chart.
*/}}
{{- define "unified-api-dashboard.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "unified-api-dashboard.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "unified-api-dashboard.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "unified-api-dashboard.labels" -}}
helm.sh/chart: {{ include "unified-api-dashboard.chart" . }}
{{ include "unified-api-dashboard.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "unified-api-dashboard.selectorLabels" -}}
app.kubernetes.io/name: {{ include "unified-api-dashboard.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "unified-api-dashboard.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "unified-api-dashboard.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the name of the configmap to use
*/}}
{{- define "unified-api-dashboard.configName" -}}
{{- printf "%s-config" (include "unified-api-dashboard.fullname" .) }}
{{- end }}

{{/*
Create the name of the secret to use
*/}}
{{- define "unified-api-dashboard.secretName" -}}
{{- printf "%s-secrets" (include "unified-api-dashboard.fullname" .) }}
{{- end }}

{{/*
Create the name of the logs PVC to use
*/}}
{{- define "unified-api-dashboard.logsPvcName" -}}
{{- printf "%s-logs" (include "unified-api-dashboard.fullname" .) }}
{{- end }}

{{/*
Create the name of the cache PVC to use
*/}}
{{- define "unified-api-dashboard.cachePvcName" -}}
{{- printf "%s-cache" (include "unified-api-dashboard.fullname" .) }}
{{- end }}

{{/*
Create the image path
*/}}
{{- define "unified-api-dashboard.image" -}}
{{- $registry := default .Values.image.registry .Values.global.imageRegistry }}
{{- $repository := .Values.image.repository }}
{{- $tag := default .Chart.AppVersion .Values.image.tag }}
{{- if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag }}
{{- else }}
{{- printf "%s:%s" $repository $tag }}
{{- end }}
{{- end }}

{{/*
Return the proper image name
*/}}
{{- define "unified-api-dashboard.imagePullPolicy" -}}
{{- if .Values.image.pullPolicy }}
{{- .Values.image.pullPolicy }}
{{- else if semverCompare ">=1.17.0" .Capabilities.KubeVersion.GitVersion }}
{{- "Always" }}
{{- else }}
{{- "IfNotPresent" }}
{{- end }}
{{- end }}
