# SPDX-License-Identifier: Apache-2.0
# Copyright 2023 The HuggingFace Authors.

{{- define "initContainerDescriptiveStatistics" -}}
- name: prepare-descriptive-statistics
  image: ubuntu:focal
  imagePullPolicy: {{ .Values.images.pullPolicy }}
  command: ["/bin/sh", "-c"]
  args:
  - chown {{ .Values.uid }}:{{ .Values.gid }} /mounted-path;
  volumeMounts:
  - mountPath: /mounted-path
    mountPropagation: None
    name: volume-descriptive-statistics
    subPath: "{{ include "descriptiveStatistics.subpath" . }}"
    readOnly: false
  securityContext:
    runAsNonRoot: false
    runAsUser: 0
    runAsGroup: 0
{{- end -}}
