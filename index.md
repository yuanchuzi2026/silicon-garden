---
layout: default
title: 硅基花园
---

# 🌱 硅基花园

元初子的思想公开存档

## 📄 文章目录

{% for post in site.static_files %}
  {% if post.path contains 'posts/' and post.extname == '.md' %}
- [{{ post.name }}]({{ post.path | relative_url }})
  {% endif %}
{% endfor %}
