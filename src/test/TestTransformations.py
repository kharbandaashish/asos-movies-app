import os
import sys
import logging
import unittest
import warnings
from pyspark.sql.types import *
from pyspark.sql import SparkSession

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(1, ROOT_DIR)

from etl import Transformations


class TestTransformations(unittest.TestCase):
    trn = None
    database_name = "movies_data_test"

    @classmethod
    def setUp(self):
        warnings.filterwarnings("ignore", category=ResourceWarning)
        self.logger = logging.getLogger()
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(logging.Formatter('[%(asctime)s] - %(levelname)s - %(message)s'))
        logging.getLogger('').addHandler(console)
        self.spark = SparkSession.builder.appName("Transformations-Tests").getOrCreate()
        self.spark.sql("CREATE DATABASE IF NOT EXISTS {};".format(self.database_name))
        self.trn = Transformations

    @classmethod
    def tearDownClass(self):
        self.spark.sql("DROP DATABASE {} CASCADE;".format(self.database_name))
        self.spark.stop()

    def test_split_movies_genres(self):
        """
        Tests data generated by split_movies_genres function in Tranformations.py
        """
        movies_table_name = "movies"
        output_table_name = "exploded_movies"
        df1 = self.spark.createDataFrame(
            ([1, "alpha", "crime|thriller"], [2, "beta", "crime"], [3, "delta", "thriller"]),
            ["movieId", "title", "genres"])
        df1.write.mode("overwrite").format("delta").saveAsTable("{}.{}".format(self.database_name, movies_table_name))
        self.trn.split_movies_genres(self.logger, self.spark, self.database_name, movies_table_name, output_table_name)
        actucal_output = self.spark.table("{}.{}".format(self.database_name, output_table_name)).sort("movieId",
                                                                                                      "genre").collect()
        expected_output = self.spark.createDataFrame(
            ([1, "alpha", "crime"], [1, "alpha", "thriller"], [2, "beta", "crime"], [3, "delta", "thriller"]),
            ["movieId", "title", "genre"]).sort("movieId", "genre").collect()
        self.assertEqual(actucal_output, expected_output)

    # test case to validate result generated by top10Movies
    def test_top_10_movies(self):
        """
        Tests data generated by top_10_movies function in Tranformations.py
        """
        movies_table_name = "movies1"
        ratings_table_name = "ratings1"
        output_file = "/test/top_10"
        df1 = self.spark.createDataFrame(
            ([1, "alpha", "crime|thriller"], [2, "beta", "crime"], [4, "alpha", "thriller"], [3, "delta", "thriller"]),
            ["movieId", "title", "genres"])
        df1.write.mode("overwrite").format("delta").saveAsTable("{}.{}".format(self.database_name, movies_table_name))
        df2 = self.spark.createDataFrame(([1, 1, 4.5, "964982703"], [1, 2, 4.0, "998787858"], [2, 1, 3.0, "901787858"],
                                          [3, 1, 4.5, "884982703"], [4, 1, 4.5, "901982703"], [5, 1, 4.5, "964882703"],
                                          [2, 2, 4.5, "964977703"], [1, 1, 4.5, "964982711"], [7, 1, 4.5, "968582703"]),
                                         ["userId", "movieId", "rating", "timestamp"])
        df2.write.mode("overwrite").format("delta").saveAsTable("{}.{}".format(self.database_name, ratings_table_name))
        self.trn.top_10_movies(self.logger, self.spark, self.database_name, movies_table_name, ratings_table_name,
                               output_file)
        actucal_output = self.spark.read.csv(output_file, header=True).select("title").collect()
        schema = StructType([
            StructField('title', StringType(), True)
        ])
        expected_output = self.spark.createDataFrame((["alpha"],), schema=schema).collect()

        self.assertEqual(actucal_output, expected_output)


if __name__ == "__main__":
    unittest.main()
