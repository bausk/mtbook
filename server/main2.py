import os, sys
from flask import Flask, request, jsonify, abort
import logging
import elasticsearch

from .config import CONFIG

app = Flask(__name__)
LOCAL_KEY = CONFIG['LOCAL']['key']

logger = logging.getLogger(__file__)
logger.setLevel(logging.DEBUG)


@app.route("/api/callback/<uuid>/<idx_name>", methods=['POST'])
def put_es(uuid, idx_name):
    if uuid == LOCAL_KEY:
        # Connect to elasticsearch
        eshost = CONFIG['ES']['host']
        esuser = CONFIG['ES']['username']
        essecret = CONFIG['ES']['secret']
        if eshost is None:
            es = elasticsearch.Elasticsearch()
        else:
            if esuser is None:
                es = elasticsearch.Elasticsearch([eshost])
            else:
                es = elasticsearch.Elasticsearch([eshost], http_auth=(esuser, essecret))
        data = request.get_json(force=True)
        payload = {}
        # Get image_url which is our unique id for elasticsearch
        entry_id = data.get('image_url')
        if entry_id is None:
            print("no image_url in response, aborting processing")
            abort(400)

        # Collect useful payload from the IR server
        for item in ['objects', 'humans', 'brands']:
            if item in data:
                payload[item] = data[item]

        # Find corresponding doc in index
        if 'brands' in payload:
            print("==BRANDS:== ", payload['brands'])
        index_name = CONFIG['ES'][idx_name + '_index']
        doctype = CONFIG['ES'][idx_name + '_doctype']
        retval = write_index(es, index_name, doctype, entry_id, payload)
        return retval
    else:
        raise SecurityKeyError('Not authorized', status_code=401)


@app.route("/api/callback/<uuid>", methods=['POST'])
def put_es_old(uuid):
    if uuid == LOCAL_KEY:

        # Connect to elasticsearch
        eshost = CONFIG['ES']['host']
        esuser = CONFIG['ES']['username']
        essecret = CONFIG['ES']['secret']
        if eshost is None:
            es = elasticsearch.Elasticsearch()
        else:
            if esuser is None:
                es = elasticsearch.Elasticsearch([eshost])
            else:
                es = elasticsearch.Elasticsearch([eshost], http_auth=(esuser, essecret))
        data = request.get_json(force=True)
        payload = {}
        # Get image_url which is our unique id for elasticsearch
        entry_id = data.get('image_url')
        if entry_id is None:
            print("no image_url in response, aborting processing")
            abort(400)

        # Collect useful payload from the IR server
        for item in ['objects', 'humans', 'brands']:
            if item in data:
                payload[item] = data[item]

        for idx_name in [
            (CONFIG['ES']['twitter_index'], "tweet"),
            (CONFIG['ES']['tumblr_index'], "tumblr"),
            (CONFIG['ES']['pinterest_index'], "pin")
        ]:
            print("OLD API!")
            write_index(es, idx_name[0], idx_name[1], entry_id, payload)
        return "OK", 200
    else:
        raise SecurityKeyError('Not authorized', status_code=401)


def write_index(es, index_name, doctype, entry_id, payload):
    print("SEARCH:: {}".format(index_name))
    if es.indices.exists(index_name):
        try:
            print("TRY INDEX {}:: entry id {}".format(index_name, entry_id))
            result = es.get(index=index_name, doc_type=doctype, id=entry_id)
            #print("\nBefore:\n")
            #print(result)
            queued_at = result.get('_source', {}).get('netra_queued_at')
            es.update(index=index_name, doc_type=doctype, id=entry_id,
                      body={'doc': payload}
                      )
            print("Queued at {} -> WRITE OK {} entry id {}.\n".format(queued_at, index_name, entry_id))
            result = es.get(index=index_name, doc_type=doctype, id=entry_id)
            #print("\nAfter:\n")
            #print(result)
        except elasticsearch.ElasticsearchException:
            if es.indices.exists_type(index=index_name, doc_type=doctype):
                es.create(index=index_name, doc_type=doctype, id=entry_id,
                          body=payload
                          )
            else:
                print("FAIL {}:: entry id {} failed.\n".format(index_name, entry_id))
    else:
        print("FAIL:: index {} not found!\n".format(index_name))
        return "Index not found", 404
    return "OK", 200


class SecurityKeyError(Exception):
    status_code = 401

    def __init__(self, message, status_code=None, payload=None):
        Exception.__init__(self)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        self.payload = payload

    def to_dict(self):
        rv = dict(self.payload or ())
        rv['message'] = self.message
        return rv


@app.errorhandler(SecurityKeyError)
def handle_security_error(error):
    response = jsonify(error.to_dict())
    response.status_code = error.status_code
    return response


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=9000)
