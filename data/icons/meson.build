app_id = '.'.join([domain, author, meson.project_name()])

scalable_dir = join_paths('hicolor', 'scalable', 'apps')
install_data(
  join_paths(('@0@.svg').format(app_id)),
  install_dir: join_paths(get_option('datadir'), 'icons', scalable_dir)
)
