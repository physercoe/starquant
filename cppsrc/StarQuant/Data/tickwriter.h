#ifndef __StarQuant_Data_TickWriter_H__
#define __StarQuant_Data_TickWriter_H__

#include <condition_variable>
#include <mutex>
#include <Common/config.h>
#include <Common/util.h>
#include <Common/datastruct.h>

#include <APIs/Ctp/ThostFtdcUserApiDataType.h>
#include <APIs/Ctp/ThostFtdcUserApiStruct.h>
#include <APIs/Tap/TapQuoteAPIDataType.h>
#include <APIs/Tap/TapAPICommDef.h>

//#include <bson.h>
//#include <bson/bcon.h>
#include <bson/bson.h>
#include <mongoc.h>
#include <time.h>

using std::mutex;

//////////////////////////////////////////////////////////////////////////
// tick recorder
//////////////////////////////////////////////////////////////////////////
namespace StarQuant
{
    struct TickWriter {
        int bufSize;
        FILE* fp = nullptr;
        int count = 0; //length of string in the buffer
        char* head = nullptr; // = raiibuf.get();
// mongodb writer
          //mongoc_client_t      *client;
           //mongoc_database_t    *database;
           //mongoc_collection_t  *collection;
           //bson_t  *command,  reply, *insert;
           bson_error_t          error;
        mongoc_client_pool_t *pool;
        mongoc_uri_t         *uri;

        TickWriter() {
            bufSize = 1024;
            head = new char[bufSize];
            mongoc_init ();
            uri = mongoc_uri_new("mongodb://localhost:27017");
            pool = mongoc_client_pool_new(uri);
            //client = mongoc_client_new ("mongodb://localhost:27017");
            //database = mongoc_client_get_database (client, "findata");
         }
        ~TickWriter() {
            if (fp) {
                fwrite(head, sizeof(char), count, fp);
                fflush(fp);
                fclose(fp);
            }
            delete[] head;
//			mongoc_collection_destroy (collection);
//			mongoc_database_destroy (database);
//			mongoc_client_destroy (client);
            mongoc_client_pool_destroy(pool);
            mongoc_uri_destroy(uri);
            mongoc_cleanup ();
        }

        void put(const string& _str) {
            if (!_str.empty()) {
                char tmp[512] = {};
                //sprintf(tmp, "%lu@%s\n", getMicroTime(), _str.c_str());
                sprintf(tmp, "%s @%s\n", ymdhmsf().c_str(), _str.c_str());
                uint32_t strsize = strlen(tmp); // + 1;
                uint32_t required_buffer_len = count + strsize;

                if (required_buffer_len > bufSize) {
                    size_t r = fwrite(head, sizeof(char), count, fp);
                    //printf("write files\n");
                    if (r == count) {
                        memcpy(head, tmp, strsize * sizeof(char));
                        count = strsize;
                        fflush(fp);
                        return;
                    }
                    else {
                        //error
                        //http://www.cplusplus.com/reference/cstdio/fwrite/
                    }
                }
                memcpy(head + count, tmp, strsize * sizeof(char));
                count = required_buffer_len;
            }
        }

        void insertdb(const string& _str){
            if (!_str.empty()) {
                vector<string> vs = stringsplit(_str, SERIALIZATION_SEPARATOR);
                if ((MSG_TYPE)(atoi(vs[0].c_str())) == MSG_TYPE::MSG_TYPE_TICK_L1)		
                {
                    
                    vector<string> fullsym = stringsplit(vs[1], ' ');
                    string  collectionname = fullsym[2]; 
                    mongoc_client_t     *client = mongoc_client_pool_pop(pool);
                    mongoc_collection_t *collection = mongoc_client_get_collection (client, "findata", collectionname.c_str());

                    bson_t *doc = bson_new();
                    BSON_APPEND_UTF8(doc, "contractno", fullsym[3].c_str());
                    BSON_APPEND_DATE_TIME(doc, "datetime", string2unixtimems(vs[2])+8*3600000);
                    BSON_APPEND_DOUBLE(doc, "price", atof(vs[3].c_str()));
                    BSON_APPEND_INT32(doc, "size", atoi(vs[4].c_str()));
                    BSON_APPEND_DOUBLE(doc, "bidprice1", atof(vs[5].c_str()));
                    BSON_APPEND_INT32(doc, "bidsize1", atoi(vs[6].c_str()));
                    BSON_APPEND_DOUBLE(doc, "askprice1", atof(vs[7].c_str()));
                    BSON_APPEND_INT32(doc, "asksize1", atoi(vs[8].c_str()));
                    BSON_APPEND_INT32(doc, "openinterest", atoi(vs[9].c_str()));
                    BSON_APPEND_INT32(doc, "dominant", 0);
//					BSON_APPEND_DOUBLE(doc, "upperLimit", atof(vs[14].c_str()));
//					BSON_APPEND_DOUBLE(doc, "lowerLimit", atof(vs[15].c_str()));
                    // 将bson文档插入到集合
                    if (!mongoc_collection_insert(collection, MONGOC_INSERT_NONE, doc, NULL, &error)) {
                        fprintf(stderr, "Count failed: %s\n", error.message);
                    }
                    bson_destroy(doc);
                    mongoc_collection_destroy(collection);
                    mongoc_client_pool_push(pool, client);
                }
                else if ((MSG_TYPE)(atoi(vs[0].c_str())) == MSG_TYPE::MSG_TYPE_TICK_L5){
                    // Tick_L5 k;
                    // k.fullsymbol_ = vs[1];
                    // k.time_ = vs[2];
                    // k.price_ = atof(vs[3].c_str());
                    // k.size_ = atoi(vs[4].c_str());
                    // k.depth_ = 5;
                    // k.bidprice_L1_ = atoi(vs[5].c_str());
                    // k.bidsize_L1_ = atoi(vs[6].c_str());
                    // k.askprice_L1_ = atoi(vs[7].c_str());
                    // k.asksize_L1_ = atoi(vs[8].c_str());
                    // k.bidprice_L2_ = atoi(vs[9].c_str());
                    // k.bidsize_L2_ = atoi(vs[10].c_str());
                    // k.askprice_L2_ = atoi(vs[11].c_str());
                    // k.asksize_L2_ = atoi(vs[12].c_str());
                    // k.bidprice_L3_ = atoi(vs[13].c_str());
                    // k.bidsize_L3_ = atoi(vs[14].c_str());
                    // k.askprice_L3_ = atoi(vs[15].c_str());
                    // k.asksize_L3_ = atoi(vs[16].c_str());
                    // k.bidprice_L4_ = atoi(vs[17].c_str());
                    // k.bidsize_L4_ = atoi(vs[18].c_str());
                    // k.askprice_L4_ = atoi(vs[19].c_str());
                    // k.asksize_L4_ = atoi(vs[20].c_str());
                    // k.bidprice_L5_ = atoi(vs[21].c_str());
                    // k.bidsize_L5_ = atoi(vs[22].c_str());
                    // k.askprice_L5_ = atoi(vs[23].c_str());
                    // k.asksize_L5_ = atoi(vs[24].c_str());
                    // k.open_interest = atoi(vs[25].c_str());
                    // k.open_ = atoi(vs[26].c_str());
                    // k.high_ = atoi(vs[27].c_str());
                    // k.low_ = atoi(vs[28].c_str());
                    // k.pre_close_ = atoi(vs[29].c_str());
                    // k.upper_limit_price_ = atoi(vs[30].c_str());
                    // k.lower_limit_price_ = atoi(vs[31].c_str());

                }

            }
        }

        void insertdb(const Tick& k){
            vector<string> fullsym = stringsplit(k.fullSymbol_, ' ');
            string  collectionname = fullsym[2]; 
            mongoc_client_t     *client = mongoc_client_pool_pop(pool);
            mongoc_collection_t *collection = mongoc_client_get_collection (client, "findata", collectionname.c_str());

            bson_t *doc = bson_new();
            BSON_APPEND_UTF8(doc, "contractno", fullsym[3].c_str());
            BSON_APPEND_DATE_TIME(doc, "datetime", string2unixtimems(k.time_)+8*3600000);
            BSON_APPEND_DOUBLE(doc, "price", k.price_);
            BSON_APPEND_INT32(doc, "size", k.size_);
            BSON_APPEND_DOUBLE(doc, "bidprice1", k.bidPrice_[0]);
            BSON_APPEND_INT32(doc, "bidsize1", k.bidSize_[0]);
            BSON_APPEND_DOUBLE(doc, "askprice1", k.askPrice_[0]);
            BSON_APPEND_INT32(doc, "asksize1", k.askSize_[0]);
            BSON_APPEND_INT32(doc, "openinterest", k.openInterest_);
            BSON_APPEND_INT32(doc, "dominant", 0);
            //BSON_APPEND_DOUBLE(doc, "upperLimit", k.upper_limit_price_);
            //BSON_APPEND_DOUBLE(doc, "lowerLimit", k.lower_limit_price_);
            if (!mongoc_collection_insert(collection, MONGOC_INSERT_NONE, doc, NULL, &error)) {
                cout<<"insert mongodb failed, errormsg = "<<error.message;
            }
            bson_destroy(doc);
            mongoc_collection_destroy(collection);
            mongoc_client_pool_push(pool, client);			
        }


    };
}

#endif
