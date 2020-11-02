import React from 'react';
import Head from 'next/head';
import AppBar from '@material-ui/core/AppBar';
import Toolbar from '@material-ui/core/Toolbar';
import Typography from '@material-ui/core/Typography';

import PropTypes from 'prop-types';
import styled from '@emotion/styled';

const Container = styled.div`
  margin-top: 65px;
`;

export default function Layout({title = '计数器', children, ...props}) {
  return (
    <div>
      <Head>
        <title>{title}</title>
      </Head>
      <div>
        <AppBar position="fixed">
          <Toolbar>
            <Typography type="title" color="inherit">
              计数器
            </Typography>
          </Toolbar>
        </AppBar>
        <Container>
          {children}
        </Container>
      </div>
    </div>
  );
}

Layout.propTypes = {
  title: PropTypes.string,
  children: PropTypes.node,
};
