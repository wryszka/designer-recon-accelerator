-- Auto Loader: folder → table. Drop a new Excel in the folder and it appends. That's the whole flow.
CREATE OR REFRESH STREAMING TABLE al_landing_demo AS
SELECT *, _metadata.file_name AS source_file
FROM STREAM read_files(
  '/Volumes/lr_dev_aws_us_catalog/designer_recon_demo/recon_landing/autoloader_demo/landing',
  format => 'excel', headerRows => 1, schemaEvolutionMode => 'none');
