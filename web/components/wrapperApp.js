import React, { cloneElement } from 'react';
import Cookies from 'js-cookie';
import { User } from '../src/api/user';
import { useRouter } from 'next/router';
import PropTypes from 'prop-types';


export default (Component, requireLogin = false) => {
  function HComponent({children, userInfo, token, ...props}) {
    const user = new User({ token, userInfo });
    const child = children ? cloneElement(children, { user, ...props }): null;

    return (
      <Component {...props} user={user}>
        {child}
      </Component>
    );
  }

  HComponent.getInitialProps = async ({req, res, ...ctx}) => {
    let token;
    if (req) {
      if (req.cookies) {
        token = req.cookies.token;
      }
    } else {
      token = Cookies.get('token');
    }
    let userInfo = null;
    if (!req) {
      try {
        const info = window.localStorage.getItem('userInfo');
        if (info) {
          userInfo = JSON.parse(info);
          if (userInfo.expiredAt < new Date() / 1000) {
            userInfo = null;
          }
        }
      } catch (e) {
        userInfo = null;
      }
    }
    const user = new User({ token, userInfo });
    if (!userInfo) {
      try {
        userInfo = await user.getInfo();
        userInfo.expiredAt = Math.floor(new Date() / 1000) + 3600;
        if (!req) {
          window.localStorage.setItem('userInfo', JSON.stringify(userInfo));
        }
      } catch (e) {
        userInfo = null;
      }
    }

    if (requireLogin && !userInfo) {
      if (res) {
        res.redirect('/signin');
      } else {
        useRouter().push('/signin');
      }
      const err = new Error('Redirect to /signin');
      err.cancelled = true;
      throw err;
    }
    let props = ctx;
    if (Component.getInitialProps) {
      props = await Component.getInitialProps({ req, res, user, ...ctx });
    }
    return { ...props, userInfo, token };
  };

  HComponent.propTypes = {
    token: PropTypes.string,
    children: PropTypes.node,
    userInfo: PropTypes.object,
  };

  return HComponent;
};
