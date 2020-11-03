import React from 'react';
import PropTypes from 'prop-types';
import Head from 'next/head';
import {ThemeProvider} from '@material-ui/core/styles';
import {CacheProvider} from '@emotion/core';
import CssBaseline from '@material-ui/core/CssBaseline';
import createCache from '@emotion/cache';
import theme from '../src/theme';
import Cookies from 'js-cookie';
import {User} from '../src/api/user';

export const cache = createCache();

export default function MyApp(props) {
  const {Component, pageProps} = props;
  if (pageProps.user) {
    const {token, userInfo} = pageProps;
    const user = new User({token, userInfo});
    pageProps.user = user;
  }

  React.useEffect(() => {
    // Remove the server-side injected CSS.
    const jssStyles = document.querySelector('#jss-server-side');
    if (jssStyles) {
      jssStyles.parentElement.removeChild(jssStyles);
    }
  }, []);

  return (
    <CacheProvider value={cache}>
      <Head>
        <title>计数器</title>
        <meta name="viewport" content="initial-scale=1, width=device-width" />
      </Head>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Component {...pageProps} />
      </ThemeProvider>
    </CacheProvider>
  );
}

MyApp.propTypes = {
  Component: PropTypes.elementType.isRequired,
  pageProps: PropTypes.object.isRequired,
};

MyApp.getInitialProps = async ({Component, ctx, ...other}) => {
  const {req, res} = ctx;
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
  const user = new User({token, userInfo});
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

  if (Component.requireLogin && !userInfo) {
    if (res) {
      res.writeHead(307, {Location: '/signin'});
      res.end();
    } else {
      if (!req) {
        window.location.href = '/signin';
      }
    }
    const err = new Error('Redirect to /signin');
    err.cancelled = true;
    throw err;
  }
  let pageProps = {};
  if (Component.getInitialProps) {
    pageProps = await Component.getInitialProps({
      user, Component, ctx, ...other,
    });
  }
  return {pageProps: {...pageProps, user, userInfo, token}};
};
