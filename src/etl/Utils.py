import os
import glob
import logging
import configparser
import zipfile
import urllib.request
import subprocess
from datetime import datetime
from pyspark.sql import SparkSession
from pyspark.dbutils import DBUtils


def get_logger(stream_output=False, file_name=None):
    """
    Creates a logger based on config provided and returns its object.
    """
    log_file = '{}_{}.log'.format(file_name,
                                  datetime.now().strftime('%Y%m%d%H%M%S%f'))
    logging.getLogger("py4j").setLevel(logging.INFO)
    logging.basicConfig(filename=log_file,
                        format='[%(asctime)s] - %(levelname)s - %(message)s',
                        filemode='a',
                        datefmt='%d-%b-%y %I:%M%p')
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    if type(stream_output) is bool and stream_output:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s'))
        logging.getLogger('').addHandler(console)
    return logger


def get_spark_session(logger, app_name):
    """
    Creates a spark session with the provided app name.
    """
    logger.debug("Inside get_spark_session function in Utils.py")
    spark = SparkSession.builder.appName(app_name).getOrCreate()
    return spark


def get_dbutils(logger, spark):
    """
    Creates an instance of dbutils using the spark session provided.
    """
    logger.debug("Inside get_dbutils function in Utils.py")
    dbutils = DBUtils(spark)
    return dbutils


def read_config(logger, config_file):
    """
    Reads the config file and creates a dict object with all config params.
    """
    logger.debug("Inside read_config function in Utils.py")
    configs = dict()
    config = configparser.ConfigParser()
    config.read(config_file)
    configs['dataset_url'] = config['dataset']['dataset_url']
    configs['database_name'] = config['database_tables']['database_name']
    configs['movies_table_name'] = config['database_tables']['movies_table_name']
    configs['tags_table_name'] = config['database_tables']['tags_table_name']
    configs['ratings_table_name'] = config['database_tables']['ratings_table_name']
    configs['ratings_update_table_name'] = config['database_tables']['ratings_update_table_name']
    configs['exploded_movies_table_name'] = config['database_tables']['exploded_movies_table_name']
    configs['zip_name'] = config['directory']['zip_name']
    configs['datasets_dir'] = config['directory']['datasets_dir']
    configs['output_file_dir'] = config['directory']['output_file_dir']
    configs['download_data'] = config['controls']['download_data']
    configs['staging_flag'] = config['controls']['staging_flag']
    configs['transformations_flag'] = config['controls']['transformations_flag']
    configs['show_output_flag'] = config['controls']['show_output_flag']
    return configs


def download_dataset(logger, url, download_dir):
    """
    Downloads the dataset from provided URL to provided directory.
    """
    logger.debug("Inside download_dataset function in Utils.py")
    urllib.request.urlretrieve(url, download_dir)
    logger.info("Dataset downloaded successfully")


def unzip_dataset(logger, zip_dir, unzip_dir):
    """
    Unzips the provided dataset zip file in provided directory.
    """
    logger.debug("Inside unzip_dataset function in Utils.py")
    with zipfile.ZipFile(zip_dir, 'r') as z:
        z.extractall(unzip_dir)
    logger.info("Dataset unzipped in directory - {}".format(unzip_dir))


def upload_files_to_dbfs(logger, source_dir, target_dir):
    """
    Uploads provided files to provided directory in dbfs
    """
    logger.debug("Inside upload_files_to_dbfs function in Utils.py")
    try:
        subprocess.run(["dbfs", "cp", source_dir, target_dir, "--recursive", "--overwrite"], check=True)
    except Exception as e:
        logger.error(e)
        return False
    logger.info("Uploaded {} to {}".format(source_dir, target_dir))
    return True


def download_files_from_dbfs(logger, source_dir, target_dir):
    """
    Downloads provided files from dbfs to provided directory.
    """
    logger.debug("Inside download_files_from_dbfs function in Utils.py")
    try:
        subprocess.run(["dbfs", "cp", source_dir, target_dir, "--recursive", "--overwrite"], check=True)
    except Exception as e:
        logger.error(e)
        return False
    logger.info("Downloaded {} to {}".format(source_dir, target_dir))
    return True


def rename_and_clean_output(logger, file_dir, file_name):
    """
    Deletes _commit and _success files from provided directory and renames the part csv file to provided name.
    """
    logger.debug("Inside rename_and_clean_output function in Utils.py")
    for filename in glob.glob(file_dir+'/_*'):
        os.remove(filename)
    f = glob.glob(file_dir+'/part-*')
    if f:
        file_name = "{}_{}.csv".format(file_name, datetime.now().strftime('%Y%m%d%H%M%S'))
        os.rename(f[0], os.path.join(file_dir, file_name))
    logger.info("Output cleaned and renamed")


def cleanup(logger):
    """
    Cleans the dbfs used during the etl process.
    """
    logger.debug("Inside cleanup function in Utils.py")
    try:
        subprocess.run(["dbfs", "rm", "dbfs:/ml-latest-small", "--recursive"], check=True)
        subprocess.run(["dbfs", "rm", "dbfs:/part-123", "--recursive"], check=True)
    except Exception as e:
        logger.error(e)
    logger.info("Cleanup complete")


