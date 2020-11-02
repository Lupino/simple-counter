import { host } from '../config';

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
      { method: 'POST', body: { name, remark, extra } });
  }

  async destory() {
    return this._user.fetchJSON(`${host}/api/counters/${this.info.id}/`, {method: 'DELETE'});
  }

  async incr(step, reason='') {
    return this._user.fetchJSON(`${host}/api/counters/${this.info.id}/histories/`,
      {method: 'POST', body: { step, reason }});
  }

  async getHistoryList({ offset = 0, size = 10 }) {
    return this.fetchJSON(`${host}/api/counters/${this.info.id}/histories/?offset=${offset}&size=${size}`);
  }

  async reload() {
    this.info = await this._user.fetchJSON(`${host}/api/counters/${this.info.id}/`);
  }
}
