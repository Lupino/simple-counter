import {host} from '../config';

export default class {
  constructor(user, info) {
    this._user = user;
    this.info = info;
  }
  async update({name, remark, extra}) {
    if (extra) {
      extra = JSON.stringify(extra);
    }
    return this._user.fetchJSON(`${host}/api/counters/${this.info.id}/`,
      {method: 'POST', body: {name, remark, extra}});
  }

  async destory() {
    return this._user.fetchJSON(`${host}/api/counters/${this.info.id}/`,
      {method: 'DELETE'});
  }

  async incr(step, reason='') {
    const pathname = `${host}/api/counters/${this.info.id}/histories/`;
    return this._user.fetchJSON(pathname,
      {method: 'POST', body: {step, reason}});
  }

  async getHistoryList({offset = 0, size = 10}) {
    const pathname = `${host}/api/counters/${this.info.id}/histories/`;
    return this.fetchJSON(`${pathname}?offset=${offset}&size=${size}`);
  }

  async reload() {
    const pathname = `${host}/api/counters/${this.info.id}/`;
    this.info = await this._user.fetchJSON(pathname);
  }
}
