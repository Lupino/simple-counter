import fetchJSON from 'higher-order-helper/fetchJSON';
import { host } from '../config';
import qs from 'querystring';
import Counter from './counter';

export function signin({ name, password }) {
  return fetchJSON(`${host}/api/signin/`, { method: 'POST', body: { name, password } });
}

export class User {
  constructor({ token = null, info = null }) {
    this.token = token;
    this.info = info;
  }

  async fetchJSON(url, options = {}) {
    if (this.token) {
      options.headers = options.headers || {};
      options.headers['X-REQUEST-TOKEN'] = this.token;
    }
    return fetchJSON(url, options);
  }

  async getInfo() {
    if (!this.info) {
      this.info = await this.fetchJSON(`${host}/api/users/me/`);
    }
    return this.info;
  }

  async createCounter(name, remark="") {
    const counter = await this.fetchJSON(`${host}/api/counters/`, { method: 'POST', body: { name, remark } });
    const realCounter = new Counter(this, counter);
    return realCounter;
  }
  async getCounter(cid) {
    const counter = await this.fetchJSON(`${host}/api/counters/${cid}/`);
    const realCounter = new Counter(this, counter);
    return realCounter;
  }
  async getCounterList({ offset = 0, size = 10 }) {
    return this.fetchJSON(`${host}/api/counters/?offset=${offset}&size=${size}`);
  }
}
