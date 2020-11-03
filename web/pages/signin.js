import React, { useState } from 'react';
import PropTypes from 'prop-types';
import Layout from '../components/Layout';
import wrapperApp from '../components/wrapperApp';
import { withStyles } from '@material-ui/core/styles';
import Button from '@material-ui/core/Button';
import TextField from '@material-ui/core/TextField';
import Paper from '@material-ui/core/Paper';

import {useRouter} from 'next/router';
import Cookies from 'js-cookie';
import { signin } from '../src/api/user';
import promiseToCallback from 'higher-order-helper/promiseToCallback';

const styles = theme => ({
  button: {
    margin: theme.spacing(1),
  },
  signinForm: {
    display: 'flex',
    flex: 1,
    alignItems: 'center',
    flexDirection: 'column',
    paddingTop: 20,
  },
  signinFormInner: {
    width: 500,
    paddingTop: 20,
    paddingLeft: 50,
    paddingRight: 50,
    paddingBottom: 20,
  },
  title: {
    margin: 0,
    fontWeight: 500,
  },
});

function Signin ({classes, ...props}) {
  const router = useRouter();
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [errors, setErrors] = useState({});
  const handleSignin = () => {
    let hasErr = false;
    let errors = {};
    if (!name) {
      errors.name = '请输入用户名/手机号';
      hasErr = true;
    }
    if (password.length < 6) {
      errors.password = '密码必须大于 6 位';
      hasErr = true;
    }
    if (hasErr) {
      setErrors({ errors });
      return;
    }
    promiseToCallback(signin)({name, password}, (err, info) => {
      console.log(err, info)
      if (err) {
        alert('登录失败!\n用户名或者密码错误!');
        return;
      }
      try {

      Cookies.set('token', info.token);
      window.localStorage.setItem('userInfo', JSON.stringify(info.user));
      router.push('/');
      } catch (e) {
        console.log(e)
      }
    });
  };
  return (
    <Layout title='登录' {...props}>
      <div className={classes.signinForm}>
        <Paper className={classes.signinFormInner}>
          <h3 className={classes.title}>
            登录计数器
          </h3>
          <TextField
            placeholder='请输入用户名/手机号'
            label='用户名/手机号'
            margin="normal"
            fullWidth
            value={name}
            onChange={({target}) => {
              setName(target.value);
              setErrors({...errors, name: null});
            }}
            InputLabelProps={{shrink: true}}
            error={!!errors.name}
            helperText={errors.name}
          />
          <TextField
            placeholder='请输入密码'
            label='密码'
            fullWidth
            type='password'
            value={password}
            onChange={({target}) => {
              setPassword(target.value);
              setErrors({...errors, password: null});
            }}
            margin="normal"
            InputLabelProps={{shrink: true}}
            error={!!errors.password}
            helperText={errors.password}
          />

          <br />
          <br />
          <Button variant="contained" color="primary" onClick={handleSignin}>登录</Button>
        </Paper>
      </div>
    </Layout>
  );
}

Signin.propTypes = {
  classes: PropTypes.object
};

export default withStyles(styles)(Signin);
