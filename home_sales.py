
# Home Sales SparkSQL Challenge


## Setup


### Spark for Colab


import os

# Find the latest version of spark 3.x  from http://www.apache.org/dist/spark/ and enter as the spark version
spark_version = 'spark-3.5.5'
os.environ['SPARK_VERSION'] = spark_version

# Install Spark and Java
!apt-get update
!apt-get install openjdk-11-jdk-headless -qq > /dev/null
!wget -q http://www.apache.org/dist/spark/$SPARK_VERSION/$SPARK_VERSION-bin-hadoop3.tgz
!tar xf $SPARK_VERSION-bin-hadoop3.tgz
!pip install -q findspark

# Set Environment Variables
os.environ['JAVA_HOME'] = '/usr/lib/jvm/java-11-openjdk-amd64'
os.environ['SPARK_HOME'] = f'/content/{spark_version}-bin-hadoop3'

# Start a SparkSession
import findspark
findspark.init()


### Import dependencies


# Import packages
from pyspark import SparkFiles
from pyspark.sql import SparkSession
import time

# Create a SparkSession
spark = SparkSession.builder.appName('SparkSQL').getOrCreate()


## Main Challenge


### Extract data from AWS S3 Bucket


# 1. Read the home_sales_revised.csv from the provided AWS S3 bucket location into a PySpark DataFrame.
url = 'https://2u-data-curriculum-team.s3.amazonaws.com/dataviz-classroom/v1.2/22-big-data/home_sales_revised.csv'

spark.sparkContext.addFile(url)
df = spark.read.csv(SparkFiles.get('home_sales_revised.csv'), sep = ',', header = True, inferSchema = True)


### Take a look at the data


# (check to make sure schema was read in properly)
df.printSchema()


# Examining summary of dataset
df.show(5)


### SparkSQL Begins Here


# 2. Create a temporary view of the DataFrame.
df.createOrReplaceTempView('home_sales')


# 3. What is the average price for a four bedroom house sold per year, rounded to two decimal places?
query = (
    '''
    SELECT
        YEAR(date) AS year,
        ROUND(AVG(price), 2) AS avg_price
    FROM
        home_sales
    WHERE
        bedrooms = 4
    GROUP BY
        YEAR(date)
    '''
)
spark.sql(query).show()


# 4. What is the average price of a home for each year the home was built,
# that have 3 bedrooms and 3 bathrooms, rounded to two decimal places?
query = (
    '''
    SELECT
        date_built AS year_built,
        ROUND(AVG(price), 2) AS avg_price
    FROM
        home_sales
    WHERE
        bedrooms = 3 AND
        bathrooms = 3
    GROUP BY
        date_built
    '''
)

spark.sql(query).show()


# 5. What is the average price of a home for each year the home was built,
# that have 3 bedrooms, 3 bathrooms, with two floors,
# and are greater than or equal to 2,000 square feet, rounded to two decimal places?
query = (
    '''
    SELECT
        date_built AS year_built,
        ROUND(AVG(price), 2) AS avg_price
    FROM
        home_sales
    WHERE
        bedrooms = 3 AND
        bathrooms = 3 AND
        floors = 2 AND
        sqft_living >= 2000
    GROUP BY
        date_built
    '''
)

spark.sql(query).show()


# 6. What is the average price of a home per "view" rating, rounded to two decimal places,
# having an average home price greater than or equal to $350,000? Order by descending view rating.
# Although this is a small dataset, determine the run time for this query.

start_time = time.time()

main_query = (
    '''
    SELECT
        view,
        ROUND(AVG(price), 2) AS avg_price
    FROM
        home_sales
    GROUP BY
        view
    HAVING
        avg_price >= 350000
    ORDER BY
        view DESC
    '''
)

spark.sql(main_query).show()

uncached_time = time.time() - start_time
print("--- %s seconds ---" % uncached_time)


### Caching & Optimization


#### Create a cache and verify


# 7. Cache the the temporary table home_sales.
spark.sql('CACHE TABLE home_sales')


# 8. Check if the table is cached.
spark.catalog.isCached('home_sales')


# 9. Using the cached data, run the last query above, that calculates
# the average price of a home per "view" rating, rounded to two decimal places,
# having an average home price greater than or equal to $350,000.
# Determine the runtime and compare it to the uncached runtime.

start_time = time.time()

spark.sql(main_query).show()

cached_time = time.time() - start_time
print("--- %s seconds ---" % cached_time)


diff = 0.759019136428833 - 0.4863274097442627
print(f'Time difference between cached run and uncached run was {diff} seconds.')


#### Partitioning for speed


# 10. Partition by the "date_built" field on the formatted parquet home sales data
df.write.partitionBy('date_built').mode('overwrite').parquet('partitioned_home_sales')


# 11. Read the parquet formatted data.
p_df = spark.read.parquet('partitioned_home_sales')


# 12. Create a temporary table for the parquet data.
p_df.createOrReplaceTempView('p_home_sales')


# 13. Using the parquet DataFrame, run the last query above, that calculates
# the average price of a home per "view" rating, rounded to two decimal places,
# having an average home price greater than or equal to $350,000.
# Determine the runtime and compare it to the cached runtime.

start_time = time.time()

spark.sql(main_query).show()

partitioned_time = time.time() - start_time

print("--- %s seconds ---" % partitioned_time)


#### Checking results and uncaching


part_against_cached_time = cached_time - partitioned_time
part_against_uncached_time = uncached_time - partitioned_time

print('Cached time - partitioned time: %s' % part_against_cached_time)
print('Uncached time - partitioned time: %s' % part_against_uncached_time)


# 14. Uncache the home_sales temporary table.
spark.sql('UNCACHE TABLE home_sales')


# 15. Check if the home_sales is no longer cached
spark.catalog.isCached('home_sales')





