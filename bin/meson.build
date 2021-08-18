app_id = '.'.join([domain, author, meson.project_name()])
pkgdatadir = join_paths(get_option('prefix'), get_option('datadir'), meson.project_name())
moduledir = join_paths(pkgdatadir, 'turtle')
python = import('python')

conf = configuration_data()
conf.set('PYTHON', python.find_installation('python3').path())
conf.set('VERSION', meson.project_version())
conf.set('localedir', join_paths(get_option('prefix'), get_option('localedir')))
conf.set('pkgdatadir', pkgdatadir)
conf.set('appid', app_id)

configure_file(
  input: 'turtle.in',
  output: 'turtle',
  configuration: conf,
  install: true,
  install_dir: get_option('bindir')
)

